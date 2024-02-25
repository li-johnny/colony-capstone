import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.uix.image import AsyncImage
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.properties import BooleanProperty
from kivy.graphics.texture import Texture
from kivy.graphics.transformation import Matrix
from plyer import filechooser
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from count import process_images_from_paths
import cv2 as cv


# Set app size
Window.size = (1000, 700)

# Designate our design file
Builder.load_file("style.kv")

# Store list of image paths and textures
images = []
# Store list of image containers showed in the uploaded images section
imageContainers = []
swap = 1

class ImageContainerWidget(BoxLayout):
    source = StringProperty()
    texture = ObjectProperty()

    def remove(self):
        self.parent.remove_widget(self)
        for i in range(len(images)):
            if (images[i][0] == self.source):
                del images[i]
                del imageContainers[i]
                break
    
    # Swap image with processed image and back
    def swap_image(self):
        global swap
        if (swap == 0):
            self.ids.swap.clear_widgets()
            replace = AsyncImage(texture = self.texture, size_hint = (1, 1), fit_mode = 'cover')
            self.ids.swap.add_widget(replace)
            # swap = 1
        else:
            self.ids.swap.clear_widgets()
            replace = AsyncImage(source = self.source, size_hint = (1, 1), fit_mode = 'cover')
            self.ids.swap.add_widget(replace)
            # swap = 0

class PreviewerContainer(Scatter):
    source = StringProperty(None)
    texture = None
    replace = None

    # Implements zoom functionality for previewer image
    # Code inspired from https://stackoverflow.com/questions/49807052/kivy-scroll-to-zoom
    def on_touch_down(self, touch):
        if touch.is_mouse_scrolling:
            factor = None
            if touch.button == 'scrolldown':
                if self.scale < 10:
                    factor = 1.2
            elif touch.button == 'scrollup':
                if self.scale > 1:
                    factor = 1/1.2
            if factor is not None:
                self.apply_transform(Matrix().scale(factor, factor, factor), anchor=touch.pos)
        else:
            super(PreviewerContainer, self).on_touch_down(touch)
            
    def zoom_in(self):
        if self.scale < 10:
            self.apply_transform(Matrix().scale(1.2, 1.2, 1.2), anchor=self.parent.center )
    
    def zoom_out(self):
        if self.scale > 1:
            self.apply_transform(Matrix().scale(1/1.2, 1/1.2, 1/1.2), anchor=self.parent.center )

    # Swap image with processed image and back
    def swap_image(self):
        global swap
        # Update texture value if it equals None
        if (self.texture == None):
            for i in range(len(images)):
                if (images[i][0] == self.source):
                    self.texture = images[i][1]
                    break

        if (swap == 0):
            self.ids.relativeContainer.clear_widgets()
            self.replace = AsyncImage(texture = self.texture, size = (self.parent.width, self.parent.height) )
            self.ids.relativeContainer.add_widget(self.replace)
        else:
            self.ids.relativeContainer.clear_widgets()
            self.replace = AsyncImage(source = self.source, size = (self.parent.width, self.parent.height))
            self.ids.relativeContainer.add_widget(self.replace)

    # Set image back to it's original size and position
    def reset_image(self):
        self.scale = 1
        self.pos = self.parent.pos
    

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
            imageContainer = ImageContainerWidget(source = file_path, texture = None)
            imageContainers.append(imageContainer)
            self.ids.image_box.add_widget(imageContainer)
            images.append([file_path, None])
            self.ids.prevContainer.source = file_path
            self.ids.prevContainer.ids.previewer.opacity = 1
            print(images)
        else:
            print("Could not open")
    
    # Update Image in the image previewer
    def previewer_update(self, source, texture):
        global swap
        container = self.ids.prevContainer
        container.reset_image()
        if (container.replace == None):
            container.source = source
        else:
            if(swap == 1):
                container.source = source
                container.texture = texture
                container.replace.source = source
            else:
                container.source = source
                container.texture = texture
                container.replace.texture = texture

    def activate_cancel(self):
        self.ids.process_button.text = "Process"
        self.ids.upload_button.text = "Upload"
        self.processing = True
        self.infoContainer.remove()

    def convert_to_texture(self, image):
        image = cv.flip(image, 0)

        w, h, _ = image.shape
        texture = Texture.create(size=(h, w))
        texture.blit_buffer(image.flatten(), colorfmt='rgb', bufferfmt='ubyte')

        return texture
    
    def start_processing(self):
        print("Processing started...")
        for i in images:
            if(i[1] == None):
                colonyCount, numpyImage = process_images_from_paths([i[0]])
                i[1] = self.convert_to_texture(numpyImage[0])

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
                self.ids.prevContainer.reset_image()
            else:
                self.start_exporting()
        except Exception as e:
            print(f"Error: {e}")

    # Toggle images between processed and non-processed versions
    def toggle_images(self):
        global swap
        if (swap == 0):
            swap = 1
        else:
            swap = 0

        for i in range(len(imageContainers)):
            imageContainers[i].texture = images[i][1]
            imageContainers[i].swap_image()
        
        # Toggle image in container to unprocessed/processed
        self.ids.prevContainer.swap_image()

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
