import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from plyer import filechooser
from kivy.clock import Clock
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image


# Set app size
Window.size = (1000, 700)

# Designate our design file
Builder.load_file("style.kv")

# Store list of image paths
images = []

class ImageContainerWidget(BoxLayout):
    source = StringProperty()

    def remove(self):
        self.parent.remove_widget(self)
        images.remove(self.source)

class InfoContainer(BoxLayout):
    tools_visible = BooleanProperty(False)
    toggle_state = BooleanProperty(True)

    def toggle_tools(self):
        self.tools_visible = not self.tools_visible
        self.update_ui_based_on_tools_visibility()

    def update_ui_based_on_tools_visibility(self):
        # Assuming you have an id for your edit button and tool section layout
        # For example, let's say the id for your edit button is 'edit_button'
        # and your tool section layout is 'tools_layout'
        
        if self.tools_visible:
            # Hide the edit button
            self.ids.edit_button.size_hint = (None, None)
            self.ids.edit_button.size = (0, 0)
            self.ids.edit_button.opacity = 0

            # Show the tool section
            self.ids.tools_layout.size_hint = (1, 0.2)
            self.ids.tools_layout.opacity = 1
        else:
            # Show the edit button
            self.ids.edit_button.size_hint = (1, 0.2)
            self.ids.edit_button.size = (self.parent.width, 60)  # Adjust the height as needed
            self.ids.edit_button.opacity = 1

            # Hide the tool section
            self.ids.tools_layout.size_hint = (None, None)
            self.ids.tools_layout.size = (0, 0)
            self.ids.tools_layout.opacity = 0


    def edit(self):
        print("Edit mode")
    
    def add_colony(self):
        print("Add Colony was pressed")
    
    def remove_colony(self):
        print("Remove Colony was pressed")
    
    def zoom_in(self):
        print("Zoom In was pressed")

    def zoom_out(self):
        print("Zoom Out was pressed")
    
    def full_screen(self):
        print("Full_Screen was pressed")
    
    def switch_toggle(self):
        self.toggle_state = not self.toggle_state
        print("Toggle button was pressed, state is now:", "On" if self.toggle_state else "Off")
    
    
    def remove(self):
        self.parent.remove_widget(self)



class MyGridLayout(Widget):

    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)
        self.processing = True  # Flag to indicate if it's processing or exporting
        Window.bind(on_drop_file=self.file_drop)

    # Open the file expolorer when the upload button is pressed
    def file_explorer_or_cancel(self):
        try:
            if self.processing:
                filechooser.open_file(on_selection = self.selected, multiple = True)
            else:
                self.activate_cancel()
        except Exception as e:
            print(f"Error: {e}")
        
    
    # Send dropped in images to load_image()
    def file_drop(self, window, file_path, x, y): 
        file_path = str(file_path.decode("utf-8"))
        self.load_image(file_path)

    # Send selected images to load_image()
    def selected(self, selection):
        if selection:
            for i in range(len(selection)):
                self.load_image(selection[i])

    # Add provided image to our image_box section add put in the image previewer
    def load_image(self, file_path):
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.ids.image_box.add_widget(ImageContainerWidget(source = file_path))
            images.append(file_path)
            self.ids.previewer.source = file_path
            self.ids.previewer.opacity = 1
            print(images)
        else:
            print("Could not open")
    
    # Update Image in the image previewer
    def previewer_update(self, source):
        self.ids.previewer.source = source

    def activate_cancel(self):
        self.ids.process_button.text = "Process"
        self.ids.upload_button.text = "Upload"
        self.processing = True
        self.infoContainer.remove()
    
    def start_processing(self):
        print("Processing started...")
        self.infoContainer = InfoContainer()
        self.ids.info_container.add_widget(self.infoContainer)

    def start_exporting(self):
        print("Exportinging started...")  

    def replace_with_export_and_cancel(self):
        self.ids.process_button.text = "Export"
        self.ids.upload_button.text = "Cancel"
        self.processing = False


    def on_process_button_press(self):
        try:
            if self.processing:
                self.start_processing()
                self.replace_with_export_and_cancel()
            else:
                self.start_exporting()
        except Exception as e:
            print(f"Error: {e}")

    

class ImageButton(ButtonBehavior, Image):
    pass

class CustomLayout(BoxLayout):
    pass



class colonyGUI(App):
    def build(self):
        self.myLayout = MyGridLayout()
        return self.myLayout
    
if __name__ == '__main__':
    colonyGUI().run()
