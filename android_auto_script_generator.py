import uiautomator2 as u2
import re
import time

def connect_to_device():
    """
    Attempts to connect to an Android device.

    Returns:
        u2.Device: The device object if connection is successful, None otherwise.
    """
    try:
        d = u2.connect()
        if d.info: # Check if connection is successful by getting device info
            print("Successfully connected to device.")
            return d
        else:
            # This case might not be reached if u2.connect() raises an exception on failure
            print("Failed to connect to device: No device information received.")
            return None
    except Exception as e:
        print(f"Failed to connect to device: {e}")
        return None

def get_screen_elements(device):
    """
    Analyzes the current screen and returns a list of interactable elements.

    Args:
        device (u2.Device): The uiautomator2 device object.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              properties of an interactable element.
    """
    interactable_elements = []
    processed_elements_signatures = set() # To avoid duplicates

    # Define class names that are typically editable
    EDITABLE_CLASS_NAMES = [
        "android.widget.EditText",
        "android.widget.AutoCompleteTextView",
        "android.webkit.WebView" # Web views can contain editable fields
    ]

    # Selectors for different types of interactable elements
    # We query for each type and then combine and de-duplicate.
    # Using a set for processed_elements_signatures will help in deduplication.
    # A unique signature could be a tuple of (resourceId, text, className, bounds_tuple)
    
    elements_to_check = []
    # Gather all potentially relevant elements first
    try:
        elements_to_check.extend(device(clickable=True))
        elements_to_check.extend(device(longClickable=True))
        elements_to_check.extend(device(scrollable=True))
        elements_to_check.extend(device(checkable=True))
        # For editable, we can check by className or if the 'editable' property is true
        elements_to_check.extend(device(editable=True)) 
        for class_name in EDITABLE_CLASS_NAMES:
            elements_to_check.extend(device(className=class_name))

    except Exception as e:
        print(f"Error finding elements: {e}")
        return interactable_elements

    for elem in elements_to_check:
        try:
            info = elem.info
            if not info:
                continue

            # Create a unique signature for the element to avoid duplicates
            # Bounds can be a tuple (left, top, right, bottom)
            bounds_tuple = tuple(info.get('bounds', {}).values())
            signature = (
                info.get('resourceId'),
                info.get('text'),
                info.get('className'),
                bounds_tuple,
                info.get('contentDescription')
            )

            if signature in processed_elements_signatures:
                continue
            processed_elements_signatures.add(signature)

            # Determine editable status
            is_editable = info.get('editable', False)
            if not is_editable and info.get('className') in EDITABLE_CLASS_NAMES:
                is_editable = True
            
            # Only add if it meets one of the interactable criteria based on its current state
            # This re-confirms interactability if not already covered by the initial query
            if not (info.get('clickable') or info.get('longClickable') or \
                    info.get('scrollable') or info.get('checkable') or is_editable):
                continue


            element_data = {
                'text': info.get('text', ''),
                'resource_id': info.get('resourceId', ''),
                'class_name': info.get('className', ''),
                'description': info.get('contentDescription', ''),
                'bounds': info.get('bounds', {}),
                'clickable': info.get('clickable', False),
                'long_clickable': info.get('longClickable', False),
                'scrollable': info.get('scrollable', False),
                'checkable': info.get('checkable', False),
                'checked': info.get('checked', False),
                'editable': is_editable,
                'selector': {}
            }

            # Construct selector
            res_id = element_data['resource_id']
            text = element_data['text']
            desc = element_data['description']
            class_name = element_data['class_name']

            if res_id:
                element_data['selector']['resourceId'] = res_id
            elif text:
                element_data['selector']['text'] = text
                if class_name: # Add class_name for specificity if text is used
                    element_data['selector']['className'] = class_name
            elif desc:
                element_data['selector']['description'] = desc
                if class_name: # Add class_name for specificity if description is used
                     element_data['selector']['className'] = class_name
            elif class_name: # Fallback to class_name if others are not available
                element_data['selector']['className'] = class_name
            # If no good selector can be formed, it might be an issue for reliable interaction
            # For now, we accept that some selectors might be weak

            interactable_elements.append(element_data)
        except Exception as e:
            # Catch errors for individual elements
            print(f"Error processing element: {elem.info.get('resourceId', 'N/A') if elem.info else 'N/A'}. Error: {e}")
            continue
            
    return interactable_elements

def normalize_to_snake_case(text):
    if not text:
        return "unnamed_screen"
    # Remove package paths if it looks like an activity name
    if '.' in text and text.count('.') > 1: # Heuristic for full activity names
        text = text.split('.')[-1]
    text = text.lower()
    text = re.sub(r'\s+', '_', text) # Replace spaces with underscores
    # Keep only a-z, 0-9, and underscores, remove others
    text = re.sub(r'[^a-z0-9_]', '', text) 
    text = re.sub(r'_+', '_', text) # Replace multiple underscores with single
    text = text.strip('_') # Remove leading/trailing underscores
    if not text: # If empty after stripping
        return "unnamed_screen"
    if text[0].isdigit(): # Ensure it doesn't start with a digit
        return f"screen_{text}"
    return text

def generate_screen_name(device, elements):
    """
    Generates a normalized screen name based on prominent text elements or activity name.

    Args:
        device (u2.Device): The uiautomator2 device object.
        elements (list): List of element dictionaries from get_screen_elements.

    Returns:
        str: A normalized snake_case screen name.
    """
    potential_name = ""

    # 1. Identify prominent text
    text_views = [el for el in elements if el.get('class_name') == 'android.widget.TextView' and el.get('text')]
    
    # Sort by top bound, then by left bound as a secondary criterion.
    # Elements with no bounds or invalid bounds will be placed at the end.
    text_views.sort(key=lambda el: (el.get('bounds', {}).get('top', float('inf')), el.get('bounds', {}).get('left', float('inf'))))

    # Heuristic 1: Look for resource_id commonly used for titles
    for tv in text_views:
        res_id = tv.get('resource_id', '').lower()
        if "title" in res_id or "action_bar_title" in res_id or "toolbar_title" in res_id:
            potential_name = tv.get('text')
            if potential_name:
                break
    
    # Heuristic 2: If no title-like resource_id found, pick the first non-empty text from a TextView near the top
    if not potential_name:
        for tv in text_views:
            if tv.get('text'): # Already filtered for non-empty text, but good to be explicit
                potential_name = tv.get('text')
                break # Found the topmost non-empty TextView

    # 2. Fallback to Activity Name
    if not potential_name:
        try:
            current_app = device.app_current()
            activity_name = current_app.get('activity', '')
            if activity_name:
                potential_name = activity_name
        except Exception as e:
            print(f"Could not get activity name: {e}")
            potential_name = "" # Ensure it's empty to trigger generic fallback

    # 3. Generic Fallback (will be handled by normalize_to_snake_case if potential_name is still empty)
    if not potential_name:
        potential_name = "Unnamed Screen" # normalize_to_snake_case will make this "unnamed_screen"

    # 4. Normalize the Name
    return normalize_to_snake_case(potential_name)


if __name__ == "__main__":
    device = connect_to_device()
    if not device:
        print("Exiting due to connection failure.")
    else:
        print("Successfully connected to device.")
        all_generated_functions_code = []

        while True:
            print("\nEnsure you are on the screen you want to define.")
            input("Press Enter to analyze the current screen...") # Give user time to navigate

            print("Attempting to get screen elements...")
            elements = get_screen_elements(device)
            
            if elements:
                print(f"Found {len(elements)} interactable elements.")
            else:
                print("No interactable elements found on this screen. You can still define a name and actions if you intend to add them manually later.")

            screen_name = generate_screen_name(device, elements if elements else [])
            print(f"Generated screen name: '{screen_name}'")

            actions = build_actions_for_screen(device, elements if elements else [], screen_name)
            if not actions:
                print(f"No actions recorded for screen: {screen_name}.")
            
            function_code = generate_python_function(screen_name, actions)
            
            print(f"\n--- Generated Python Function for screen: {screen_name} ---")
            print(function_code)
            print(f"--- End of Python Function for screen: {screen_name} ---")
            all_generated_functions_code.append(function_code)

            while True:
                another_screen = input("\nDo you want to define actions for another screen? (yes/no): ").strip().lower()
                if another_screen in ['yes', 'no']:
                    break
                print("Invalid input. Please enter 'yes' or 'no'.")
            
            if another_screen == 'no':
                break
            
            print("\nPlease navigate to the new screen on your device.")
            # The next input() at the start of the loop will pause for navigation.

        print("\n\n# --- All Generated Python Functions (copy this into your main automation script) ---")
        for i, func_code in enumerate(all_generated_functions_code):
            print(func_code)
            if i < len(all_generated_functions_code) - 1:
                 print("\n") # Add a newline between functions for better readability
        print("# --- End of All Generated Python Functions ---")

        helpers_string = generate_screen_recognition_helpers_string()
        print("\n\n# --- Helper functions for screen recognition (copy this into your main automation script) ---")
        print(helpers_string)
        print("# --- End of helper functions ---")

def generate_screen_recognition_helpers_string():
    """
    Generates a Python code string containing helper functions for screen recognition.
    This includes normalize_to_snake_case and get_current_screen_identifier.
    """
    normalize_code = """
def normalize_to_snake_case(text):
    if not text:
        return "unnamed_screen"
    # Attempt to import re, as it's needed.
    try:
        import re
    except ImportError:
        # This is a fallback if re is not available in the target environment,
        # though it's a standard library.
        print("Warning: 're' module not found for normalize_to_snake_case.")
        # Simple normalization without regex if re is not available
        processed_text = text.lower().replace(' ', '_')
        final_text = ''.join(c for c in processed_text if c.isalnum() or c == '_')
        if not final_text:
            return "unnamed_screen"
        if final_text[0].isdigit():
            return f"screen_{final_text}"
        return final_text

    if '.' in text and text.count('.') > 1: # Heuristic for full activity names
        text = text.split('.')[-1]
    text = text.lower()
    text = re.sub(r'\\s+', '_', text)
    text = re.sub(r'[^a-z0-9_]', '', text)
    text = re.sub(r'_+', '_', text)
    text = text.strip('_')
    if not text:
        return "unnamed_screen"
    if text[0].isdigit():
        return f"screen_{text}"
    return text
"""

    get_identifier_code = """
def get_current_screen_identifier(d):
    # Ensure re is available for normalize_to_snake_case
    try:
        import re
    except ImportError:
        # normalize_to_snake_case has a fallback if re is not found
        pass

    potential_name = ""
    
    # Heuristic 1: Look for elements with title-like resource IDs
    title_ids_patterns = [".*[Tt]itle.*", ".*action_bar_title.*", ".*toolbar_title.*"]
    for pattern in title_ids_patterns:
        try:
            # Search only for visible elements to avoid hidden titles
            title_element = d(resourceIdMatches=pattern, visible=True) 
            if title_element.exists and title_element.info.get('text'):
                potential_name = title_element.info.get('text')
                if potential_name:
                    break
        except Exception: # uiautomator2.exceptions.UiObjectNotFoundError or other
            pass # Element not found, try next pattern
    
    # Heuristic 2: If no title-like resource_id found, check first few visible TextViews
    if not potential_name:
        try:
            # Prioritize visible text views near the top of the screen
            text_views = d(className="android.widget.TextView", visible=True).all()
            # Sort by vertical position (top coordinate), then by horizontal (left coordinate)
            # This helps find elements that are visually at the "top-left" which often serve as titles
            text_views.sort(key=lambda x: (x.info['bounds']['top'], x.info['bounds']['left']))

            for i, tv in enumerate(text_views):
                if i >= 5: # Limit to checking the first 5 sorted visible TextViews
                    break
                text = tv.info.get('text')
                if text:
                    # Basic filter: not too long, not purely numeric, not identical to a previous candidate
                    if 2 < len(text) < 50 and not text.isdigit() and text != potential_name:
                        potential_name = text
                        # Consider if this is a good enough title (e.g. first non-empty, reasonably short)
                        # For simplicity, we take the first plausible one.
                        break 
        except Exception:
            pass # Error fetching or processing TextViews

    # Heuristic 3: Fallback to Activity Name
    if not potential_name:
        try:
            current_app = d.app_current()
            activity_name = current_app.get('activity', '')
            if activity_name:
                potential_name = activity_name
        except Exception: # Handle cases where d.app_current() might fail
            potential_name = ""

    # Normalize the Name
    normalized_name = normalize_to_snake_case(potential_name if potential_name else "Unnamed Screen")

    if normalized_name == "unnamed_screen" or not normalized_name:
        return "unknown_screen" # Final fallback
        
    return normalized_name
"""
    # Combine the code strings. Ensure re is imported at the top of the combined string
    # or ensure normalize_to_snake_case can handle its absence.
    # The current normalize_code string includes its own re import attempt.
    # get_identifier_code also includes an re import attempt for its call to normalize_to_snake_case.
    # For a cleaner generated output, one top-level 'import re' would be best for the string.
    
    # Let's structure it with a single import re at the top of the generated helper string.
    
    # Re-define normalize_code without its own import re for cleaner output
    normalize_code_for_helper = """
def normalize_to_snake_case(text):
    # This version assumes 're' is imported globally within the helper script
    if not text:
        return "unnamed_screen"
    if '.' in text and text.count('.') > 1:
        text = text.split('.')[-1]
    text = text.lower()
    text = re.sub(r'\s+', '_', text)  # Corrected: removed extra backslash
    text = re.sub(r'[^a-z0-9_]', '', text)
    text = re.sub(r'_+', '_', text)
    text = text.strip('_')
    if not text:
        return "unnamed_screen"
    if text[0].isdigit():
        return f"screen_{text}"
    return text
"""
    # Re-define get_identifier_code without its own import re
    get_identifier_code_for_helper = """
def get_current_screen_identifier(d):
    # This version assumes 're' is imported globally and normalize_to_snake_case is defined
    potential_name = ""
    title_ids_patterns = [".*[Tt]itle.*", ".*action_bar_title.*", ".*toolbar_title.*"]
    for pattern in title_ids_patterns:
        try:
            title_element = d(resourceIdMatches=pattern, visible=True)
            if title_element.exists and title_element.info.get('text'):
                potential_name = title_element.info.get('text')
                if potential_name: break
        except Exception: pass
    
    if not potential_name:
        try:
            text_views = d(className="android.widget.TextView", visible=True).all()
            text_views.sort(key=lambda x: (x.info['bounds']['top'], x.info['bounds']['left']))
            for i, tv in enumerate(text_views):
                if i >= 5: break
                text = tv.info.get('text')
                if text and 2 < len(text) < 50 and not text.isdigit() and text != potential_name:
                    potential_name = text
                    break
        except Exception: pass

    if not potential_name:
        try:
            activity_name = d.app_current().get('activity', '')
            if activity_name: potential_name = activity_name
        except Exception: potential_name = ""

    normalized_name = normalize_to_snake_case(potential_name if potential_name else "Unnamed Screen")
    if normalized_name == "unnamed_screen" or not normalized_name:
        return "unknown_screen"
    return normalized_name
"""

    return f"import re\n\n{normalize_code_for_helper.strip()}\n\n\n{get_identifier_code_for_helper.strip()}"


# Helper function for selector string generation
def _build_selector_string(selector_dict):
    """
    Builds a uiautomator2 selector string from a dictionary.
    Example: {'resourceId': 'com.id', 'text': 'Next'} -> 'resourceId="com.id", text="Next"'
    """
    if not selector_dict:
        return ""
    
    parts = []
    # Prioritize keys for a somewhat consistent order, though uiautomator2 is flexible
    preferred_keys = ['resourceId', 'text', 'description', 'className'] 
    
    processed_keys = set()

    for key in preferred_keys:
        if key in selector_dict and selector_dict[key]:
            parts.append(f"{key}={repr(selector_dict[key])}")
            processed_keys.add(key)
            
    # Add any other keys that might have been included (e.g. instance, if ever used)
    for key, value in selector_dict.items():
        if key not in processed_keys and value:
            parts.append(f"{key}={repr(value)}")
            
    return ", ".join(parts)

# Function to generate Python code for a screen's actions
def generate_python_function(screen_name, recorded_actions):
    function_code_lines = []
    
    function_code_lines.append(f"def {screen_name}(d):")
    function_code_lines.append(f"    \"\"\"Automates actions on the {screen_name} screen.\"\"\"")
    function_code_lines.append(f"    print(f'Executing actions for {screen_name} screen...')")
    # time import is at the top of the main script, so it's available.

    if not recorded_actions:
        function_code_lines.append("    pass")
    else:
        for action in recorded_actions:
            action_type = action['action_type']
            code_line = "    " # Indentation

            if action_type == 'click':
                selector_str = _build_selector_string(action['element_selector'])
                code_line += f"d({selector_str}).click()"
            elif action_type == 'set_text':
                selector_str = _build_selector_string(action['element_selector'])
                # repr() handles escaping quotes within the text
                code_line += f"d({selector_str}).set_text({repr(action['text'])})"
            elif action_type == 'scroll': # This is for specific element scroll using fling
                selector_str = _build_selector_string(action['element_selector'])
                direction = action['direction'] # 'up', 'down', 'left', 'right'
                # Mapping to uiautomator2 fling methods
                if direction == 'up':
                    fling_method = 'up' # d(selector).fling.up()
                elif direction == 'down':
                    fling_method = 'down' # d(selector).fling.down()
                elif direction == 'left':
                    fling_method = 'left' # d(selector).fling.left()
                elif direction == 'right':
                    fling_method = 'right' # d(selector).fling.right()
                else: # Should not happen with current input validation
                    fling_method = 'forward' 
                code_line += f"d({selector_str}).fling.{fling_method}()"
            elif action_type == 'swipe': # This is for general screen swipe
                direction = action['direction'] # 'up', 'down', 'left', 'right'
                code_line += f"d.swipe_ext(\"{direction}\")"
            elif action_type == 'scroll_to_text':
                scroll_selector_str = _build_selector_string(action['scroll_element_selector'])
                # repr() for target_text as well
                code_line += f"d({scroll_selector_str}).scroll.to(text={repr(action['target_text'])})"
                # The 'direction' in action['direction'] for scroll_to_text is for uiautomator2's scroll.to()
                # e.g. vertical_forward. If it's a simple 'forward' or 'backward', uiautomator2 handles it.
                # For now, not explicitly adding direction to scroll.to() unless required.
                # If action['direction'] needs to be passed:
                # code_line += f", direction=\"{action['direction']}\")"
            
            if code_line.strip(): # If a valid code line was generated
                function_code_lines.append(code_line)
                function_code_lines.append("    time.sleep(0.5) # Stability delay")
        
        if len(function_code_lines) <= 3: # Only def, docstring, print line
             function_code_lines.append("    pass")


    return "\n".join(function_code_lines)

# Helper functions for build_actions_for_screen
def _get_user_choice(prompt_text, min_val, max_val):
    while True:
        try:
            choice = int(input(prompt_text).strip())
            if min_val <= choice <= max_val:
                return choice
            else:
                print(f"Invalid choice. Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def _get_element_from_list(elements, prompt_text):
    if not elements:
        print("No elements available to choose from.")
        return None
    while True:
        try:
            choice = int(input(prompt_text).strip())
            if 1 <= choice <= len(elements):
                return elements[choice - 1]  # Adjust for 0-indexed list
            else:
                print(f"Invalid choice. Please enter a number between 1 and {len(elements)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def _get_element_description(element_data, default_name="element"):
    if not element_data:
        return default_name
    
    name = element_data.get('text')
    if name:
        return f"'{name}' ({element_data.get('class_name', '')})"
    
    res_id = element_data.get('resource_id')
    if res_id:
        return f"ID:'{res_id}' ({element_data.get('class_name', '')})"
        
    desc = element_data.get('description')
    if desc:
        return f"Desc:'{desc}' ({element_data.get('class_name', '')})"

    return f"{element_data.get('class_name', default_name)}"


def build_actions_for_screen(device, elements, screen_name):
    recorded_actions = []
    if not elements:
        # This print is already inside the function.
        # print(f"No interactable elements found for screen: {screen_name}. Cannot build actions.")
        return recorded_actions

    while True:
        print(f"\n--- Building actions for screen: {screen_name} ---")
        print("Found the following interactable elements:")
        for i, el in enumerate(elements):
            display_text = el.get('text') or el.get('description', '')
            display_id = el.get('resource_id', '')
            
            text_part = f"Text: '{display_text[:30]}{'...' if len(display_text) > 30 else ''}'" if display_text else ""
            id_part = f"ID: '{display_id}'" if display_id else ""
            
            desc_parts = [part for part in [text_part, id_part] if part]
            full_desc = ", ".join(desc_parts) if desc_parts else "No text/ID"
            
            print(f"  {i+1}. {el.get('class_name', 'UnknownClass')} - {full_desc}")

        print(f"\nWhat action would you like to add for {screen_name}?")
        print("  1. Click an element")
        print("  2. Enter text into an element")
        print("  3. Scroll an element (if scrollable) or the screen (swipe)")
        print("  4. Scroll until a specific text is visible (experimental)")
        print("  5. Finish and generate function for this screen")

        action_choice = _get_user_choice("Enter your choice (1-5): ", 1, 5)

        if action_choice == 5:
            print(f"Finished recording actions for {screen_name}.")
            break

        element_data = None
        # For actions 1-4, we usually need an element first.
        # For scroll_to_text (4), this is the scrollable element.
        if action_choice in [1, 2, 3, 4]:
            prompt_msg = "Which element number do you want to interact with? "
            if action_choice == 4:
                 prompt_msg = "Which element number is the SCROLLABLE container? "
            element_data = _get_element_from_list(elements, prompt_msg)
            if not element_data:
                print("No valid element selected. Try again.")
                continue
        
        action = None
        el_desc = _get_element_description(element_data)

        if action_choice == 1: # Click
            if not element_data.get('clickable'):
                 print(f"Warning: Element {el_desc} may not be clickable.")
            action = {
                'action_type': 'click',
                'element_selector': element_data['selector'],
                'description': f"Click on {el_desc}"
            }
        elif action_choice == 2: # Enter Text
            if not element_data.get('editable'):
                print(f"Error: Element {el_desc} is not editable.")
                continue
            user_text = input("Enter the text you want to input: ").strip()
            action = {
                'action_type': 'set_text',
                'element_selector': element_data['selector'],
                'text': user_text,
                'description': f"Enter text '{user_text}' into {el_desc}"
            }
        elif action_choice == 3: # Scroll/Swipe
            direction = input("Scroll direction? (up, down, left, right): ").strip().lower()
            if direction not in ['up', 'down', 'left', 'right']:
                print("Invalid direction. Defaulting to 'down'.")
                direction = 'down'
            
            if element_data.get('scrollable'):
                action = {
                    'action_type': 'scroll',
                    'element_selector': element_data['selector'],
                    'direction': direction,
                    'description': f"Scroll {el_desc} {direction}"
                }
            else:
                print(f"Element {el_desc} is not scrollable. Performing a general screen swipe {direction}.")
                action = {
                    'action_type': 'swipe', # This implies a general swipe on the screen
                    'direction': direction,
                    'description': f"Swipe screen {direction}"
                }
        elif action_choice == 4: # Scroll until text visible (Revised)
            if not element_data.get('scrollable'):
                print(f"Error: Element {el_desc} selected as scroll container is not scrollable. Please pick a scrollable element.")
                continue
            
            target_text = input("Enter the text of the element you want to scroll to find: ").strip()
            if not target_text:
                print("Target text cannot be empty. Action skipped.")
                continue
            
            # Directions for uiautomator2 scroll.to() are typically 'forward', 'backward', 
            # 'vertical_forward', 'vertical_backward', 'horizontal_forward', 'horizontal_backward'
            # We can simplify for the user or ask for specific ones.
            # The prompt asked for 'forward', 'backward', 'horiz_forward', 'horiz_backward'
            scroll_direction_options = ['forward', 'backward', 'vertical_forward', 'vertical_backward', 'horizontal_forward', 'horizontal_backward']
            direction_prompt = f"Scroll direction ({', '.join(scroll_direction_options)}): "
            direction = input(direction_prompt).strip().lower()
            if direction not in scroll_direction_options:
                print(f"Invalid scroll direction. Defaulting to 'forward'. Valid options: {scroll_direction_options}")
                direction = 'forward' # Default or choose one like vertical_forward

            action = {
                'action_type': 'scroll_to_text',
                'scroll_element_selector': element_data['selector'],
                'target_text': target_text,
                'direction': direction, # This direction is for the .scroll.to() method
                'description': f"Scroll {el_desc} {direction} until element with text '{target_text}' is visible"
            }

        if action:
            recorded_actions.append(action)
            print(f"Action added: {action['description']}")

    return recorded_actions
