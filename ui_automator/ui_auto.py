import uiautomator2 as u2

class AndroidActions:
    """
    Provides basic user action functions using uiautomator2.
    Each function validates the state of the element if applicable.
    """
    def __init__(self, device):
        self.device = device

    def understand_current_screen(self):
        """Returns current screen information (package, activity, etc.)."""
        info = self.device.info
        return info

    def tap_button(self, selector: dict):
        """Taps a button given a selector (e.g., {'text': 'Settings'})."""
        element = self.device(**selector)
        if element.exists:
            element.click()
            print(f"Tapped element: {selector}")
        else:
            print(f"Element not found: {selector}")

    def vertical_swipe(self, start_percent=0.8, end_percent=0.2, duration=0.5):
        """Performs a vertical swipe based on start and end percentages of the screen height."""
        size = self.device.window_size()
        x = size['width'] // 2
        y_start = int(size['height'] * start_percent)
        y_end = int(size['height'] * end_percent)
        self.device.swipe(x, y_start, x, y_end, duration=duration)
        print("Performed vertical swipe")

    def horizontal_swipe(self, start_percent=0.8, end_percent=0.2, duration=0.5):
        """Performs a horizontal swipe based on start and end percentages of the screen width."""
        size = self.device.window_size()
        y = size['height'] // 2
        x_start = int(size['width'] * start_percent)
        x_end = int(size['width'] * end_percent)
        self.device.swipe(x_start, y, x_end, y, duration=duration)
        print("Performed horizontal swipe")

    def enter_text(self, selector: dict, text: str):
        """Enters text into a text field specified by the selector."""
        element = self.device(**selector)
        if element.exists:
            element.set_text(text)
            print(f"Entered text in element: {selector}")
        else:
            print(f"Text field not found: {selector}")

    def toggle_on_off(self, selector: dict, desired_state=True):
        """
        Toggles a switch element.
        Checks the current 'checked' status. If it matches the desired state,
        no action is taken.
        """
        element = self.device(**selector)
        if element.exists:
            current_state = element.info.get('checked', False)
            if current_state == desired_state:
                print("Already in desired state")
            else:
                element.click()
                print("Toggled the switch")
        else:
            print("Toggle element not found:", selector)

    def select_radio_button(self, selector: dict):
        """Selects a radio button specified by the selector."""
        element = self.device(**selector)
        if element.exists:
            element.click()
            print("Selected radio button")
        else:
            print("Radio button not found:", selector)

    def hit_back(self):
        """Simulates the Back button."""
        self.device.press("back")
        print("Pressed back button")

    def go_home(self):
        """Simulates the Home button."""
        self.device.press("home")
        print("Went to home screen")

    def overflow_menu(self):
        """
        Opens the overflow menu.
        Assumes the overflow button has a content description of "More options".
        """
        element = self.device(description="More options")
        if element.exists:
            element.click()
            print("Opened overflow menu")
        else:
            print("Overflow menu not found")

    def dropdown_select(self, selector: dict, option_text: str):
        """
        Selects an option from a dropdown.
        First, it taps the dropdown element (using the selector),
        then taps the option that matches option_text.
        """
        element = self.device(**selector)
        if element.exists:
            element.click()  # Open the dropdown
            option = self.device(text=option_text)
            if option.exists:
                option.click()
                print(f"Selected dropdown option: {option_text}")
            else:
                print("Dropdown option not found:", option_text)
        else:
            print("Dropdown not found:", selector)

    def checkbox_select(self, selector: dict, desired_state=True):
        """
        Checks or unchecks a checkbox.
        Validates current state to avoid redundant clicks.
        """
        element = self.device(**selector)
        if element.exists:
            current_state = element.info.get('checked', False)
            if current_state == desired_state:
                print("Checkbox already in desired state")
            else:
                element.click()
                print("Checkbox state changed")
        else:
            print("Checkbox not found:", selector)


class ScreenInspector:
    """
    Helps inspect the current screen and generate Python code for
    actions defined in AndroidActions. It gathers information such as
    current screen name and clickable items, then waits for user input
    to generate code.
    """
    def __init__(self, device):
        self.device = device
        self.actions = AndroidActions(device)

    def get_screen_name(self):
        """Heuristically generates a screen name based on package and activity."""
        info = self.device.info
        package = info.get('currentPackageName', 'UnknownPackage')
        activity = info.get('currentActivity', 'UnknownActivity')
        return f"{package}:{activity}"

    def list_clickable_items(self):
        """
        Lists clickable items on the current screen.
        (Uses an XPath query to locate elements with clickable attribute.)
        """
        clickable_elements = self.device.xpath("//*[contains(@clickable, 'true')]").all()
        items = []
        for elem in clickable_elements:
            try:
                text = elem.attrib.get('text', '')
                if text:
                    items.append(text)
            except Exception:
                continue
        # Return unique non-empty texts
        return list(set(items))

    def generate_action_code(self, action, selector, extra_args=None):
        """
        Generates a string of Python code that calls the corresponding
        AndroidActions function.
        """
        code = ""
        if action == "tap":
            code = f"actions.tap_button({selector})"
        elif action == "swipe_vertical":
            code = "actions.vertical_swipe()"
        elif action == "swipe_horizontal":
            code = "actions.horizontal_swipe()"
        elif action == "enter_text":
            code = f"actions.enter_text({selector}, 'your_text_here')"
        elif action == "toggle_on":
            code = f"actions.toggle_on_off({selector}, desired_state=True)"
        elif action == "toggle_off":
            code = f"actions.toggle_on_off({selector}, desired_state=False)"
        elif action == "select_radio":
            code = f"actions.select_radio_button({selector})"
        elif action == "hit_back":
            code = "actions.hit_back()"
        elif action == "go_home":
            code = "actions.go_home()"
        elif action == "overflow":
            code = "actions.overflow_menu()"
        elif action == "dropdown":
            code = f"actions.dropdown_select({selector}, '{extra_args}')"
        elif action == "checkbox":
            code = f"actions.checkbox_select({selector}, desired_state={extra_args})"
        else:
            code = "# Unknown action"
        return code

    def interactive_prompt(self):
        """
        Inspects the current screen, prints the screen name and clickable items,
        then prompts you to choose an action. The generated Python code is printed to the console.
        """
        screen_name = self.get_screen_name()
        print("Current screen:", screen_name)
        clickable_items = self.list_clickable_items()
        if clickable_items:
            print("Clickable items on screen:")
            for i, item in enumerate(clickable_items):
                print(f"{i+1}. {item}")
        else:
            print("No clickable items found on screen.")

        user_choice = input("Select an item by number (for a tap action) or type a specific action (e.g., 'swipe_vertical'): ")

        # Try to treat input as a number first (tap action)
        try:
            choice_index = int(user_choice) - 1
            if 0 <= choice_index < len(clickable_items):
                selected_item = clickable_items[choice_index]
                # Create a selector based on the text attribute
                selector = f'{{"text": "{selected_item}"}}'
                code = self.generate_action_code("tap", selector)
                print("Generated Python code:")
                print(code)
            else:
                print("Invalid selection number.")
        except ValueError:
            # Not a number – assume user typed an action name.
            action = user_choice.strip()
            selector_input = input("Enter the selector as a dictionary (e.g., '{\"resourceId\": \"com.example:id/element\"}'): ")
            extra_arg = None
            if action in ["enter_text", "dropdown", "checkbox"]:
                extra_arg = input("Enter extra argument (text for enter_text/dropdown, True/False for checkbox): ")
            code = self.generate_action_code(action, selector_input, extra_arg)
            print("Generated Python code:")
            print(code)


if __name__ == "__main__":
    # Connect to the rooted Android 14 device at the provided IP address.
    d = u2.connect("172.16.4.100")
    
    # Instantiate the classes.
    actions = AndroidActions(d)
    inspector = ScreenInspector(d)
    
    # Example usage: run the interactive prompt.
    # It will print current screen info, list clickable items, then prompt you for an action.
    inspector.interactive_prompt()
