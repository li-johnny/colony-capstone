import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from plyer import filechooser

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

class MyGridLayout(Widget):

    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)
        Window.bind(on_drop_file=self.file_drop)

    # Open the file expolorer when the upload button is pressed
    def file_explorer(self):
        filechooser.open_file(on_selection = self.selected, multiple = True)
    
    # Send dropped in images to load_image()
    def file_drop(self, window, file_path, x, y): 
        file_path = str(file_path.decode("utf-8"))
        self.load_image(file_path)

    # Send selected images to load_image()
    def selected(self, selection):
        if selection:
            for i in range(len(selection)):
                self.load_image(selection[i])

    # Add provided image to our image_box section
    def load_image(self, file_path):
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            self.ids.image_box.add_widget(ImageContainerWidget(source = file_path))
            images.append(file_path)
            print(images)
        else:
            print("Could not open")
                

class colonyGUI(App):
    def build(self):
        return MyGridLayout()
    
if __name__ == '__main__':
    colonyGUI().run()
