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
from count import process_images_from_paths, annotate_image
from kivy.clock import Clock
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.label import Label
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, ListProperty


import numpy as np
import cv2 as cv


# Set app size
Window.size = (1000, 700)

# Designate our design file
Builder.load_file("style.kv")

# Store list of image containers, each item is a reference to a ImageContainerWidget
imageContainers = []
swap = 1

class ImageContainerWidget(BoxLayout):
    source = StringProperty(None)
    texture = ObjectProperty()
    numpy_image = ObjectProperty(comparator=np.array_equal)
    colonies = ObjectProperty(comparator=np.array_equal)
    is_selected = BooleanProperty(False)
    border_color = ListProperty([0, 0, 0, 0])


    def __init__(self, **kwargs):
        super(ImageContainerWidget, self).__init__(**kwargs)
        self.bind(is_selected=self.update_border_color)

    # def on_touch_down(self, touch):
    #     if self.collide_point(*touch.pos):
    #         self.is_selected = not self.is_selected
    #         if self.is_selected:
    #             self.deselect_others()
    #         # Assuming 'my_grid_layout' is a reference to your MyGridLayout instance
    #         self.my_grid_layout.previewer_update(self.source, self.texture)
    #         return True
    #     else:
    #         # Let the event propagate to other widgets
    #         return super(ImageContainerWidget, self).on_touch_down(touch)
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_selected = not self.is_selected
            if self.is_selected:
                self.deselect_others()
            self.my_grid_layout.previewer_update(self)

        return super(ImageContainerWidget, self).on_touch_down(touch)

    def update_border_color(self, instance, value):
        if self.is_selected:
            self.border_color = [0.1, 0.8, 0.8, 1]  # RGBA for blue
        else:
            self.border_color = [0, 0, 0, 0]  # Reset to transparent

    def deselect_others(self):
        for container in imageContainers:
            if container != self:
                container.is_selected = False


    def remove(self):
        # print("remove is called")
        self.parent.remove_widget(self)
        for i in range(len(imageContainers)):
            if (imageContainers[i].source == self.source):
                del imageContainers[i]
                break

    
    # Swap image with processed image and back
    def swap_image(self):
        global swap
        if (swap == 0):
            self.ids.swap.clear_widgets()
            replace = AsyncImage(texture = self.texture, size_hint = (1, 1), fit_mode = 'cover')
            self.ids.swap.add_widget(replace)
        else:
            self.ids.swap.clear_widgets()
            replace = AsyncImage(source = self.source, size_hint = (1, 1), fit_mode = 'cover')
            self.ids.swap.add_widget(replace)
    
    def previewer_update(self):
        app = App.get_running_app()
        app.root.previewer_update(self)

class PreviewerContainer(Scatter):
    imgRef = None

    replace = None
    add_mode = False
    remove_mode = False
    
    # Implements zoom functionality for previewer image
    # Code inspired from https://stackoverflow.com/questions/49807052/kivy-scroll-to-zoom
    def on_touch_down(self, touch):
        if (self.imgRef is None or self.imgRef.source == None):
            return
        
        # Finds mouse position relative to image and adds/deletes colonies
        global swap
        if ((self.add_mode or self.remove_mode) and touch.is_mouse_scrolling == False and self.parent.collide_point(*touch.pos) and swap == 0):
            mouse_pos = [touch.pos[0], touch.pos[1]]

            if (swap == 0):
                img_size = self.imgRef.texture.size
            else:
                img_size = self.ids.previewer.texture.size

            print(img_size)
            img_ratio = img_size[1]/img_size[0]

            scatter_size = self.ids.previewer.size
            scatter_ratio = scatter_size[1]/scatter_size[0]
            
            if (img_ratio > scatter_ratio):
                img_width = scatter_size[1] / img_ratio
                img_height = scatter_size[1]
            else:
                img_width = scatter_size[0]
                img_height = scatter_size[0] * img_ratio

            change = img_size[0] / img_width

            pos = self.to_local(mouse_pos[0] - ((scatter_size[0] - img_width)/2 * self.scale), mouse_pos[1] - ((scatter_size[1] - img_height)/2 * self.scale))
            pos = [change * pos[0], change * pos[1]]

            if self.add_mode:
                self.add_colony(pos)
            elif len(self.imgRef.colonies[0]) != 0:
                self.remove_colony(pos)
            print("Position relative to image (x,y): ", pos)

        # Zoom in/out and handle moving image
        if touch.is_mouse_scrolling & self.parent.collide_point(*touch.pos):
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

    def add_colony(self, pos):
        # Add colony to self.imgRef.colonies at mouse position
        array_pos = np.uint16(np.array([[pos[0], pos[1], 5]]))
        self.imgRef.colonies = np.array([np.append(self.imgRef.colonies[0], array_pos, 0)])

        # Update colony counter
        app = App.get_running_app()
        app.root.infoContainer.ids.colony_count_text.text = str(len(self.imgRef.colonies[0]))

        # Update texture being displayed
        proc = annotate_image(np.copy(self.imgRef.numpy_image[0]), self.imgRef.colonies)
        w, h, _ = proc.shape
        texture = Texture.create(size=(h, w))
        texture.blit_buffer(proc.flatten(), colorfmt='rgb', bufferfmt='ubyte')
        self.texture = texture
        self.replace.texture = texture
        for container in imageContainers:
            if (container.source == self.imgRef.source):
                container.texture = texture
                container.colonies = self.imgRef.colonies
    
    def remove_colony(self, pos):
        array_pos = np.cfloat(np.array([[pos[0], pos[1]]]))
        colin = np.delete(self.imgRef.colonies[0], 2, 1)    # delete third row of colonies with radius sizes
        colin = colin.astype(float)

        # Find nearest colony to mouse location and delete
        set = colin - array_pos
        distances = np.linalg.norm(set, axis=1)
        idx_of_nearest = np.argsort(distances)[0]

        # Checks if the cursor is within the radius of the nearest colony
        if (distances[idx_of_nearest] < self.imgRef.colonies[0][idx_of_nearest][2] + 1):
            self.imgRef.colonies = np.delete(self.imgRef.colonies, idx_of_nearest, 1)

            # Update colony counter
            app = App.get_running_app()
            app.root.infoContainer.ids.colony_count_text.text = str(len(self.imgRef.colonies[0]))

            # Updatetexture being displayed
            proc = annotate_image(np.copy(self.imgRef.numpy_image[0]), self.imgRef.colonies)
            w, h, _ = proc.shape
            texture = Texture.create(size=(h, w))
            texture.blit_buffer(proc.flatten(), colorfmt='rgb', bufferfmt='ubyte')
            self.texture = texture
            self.replace.texture = texture
            for container in imageContainers:
                if (container.source == self.imgRef.source):
                    container.texture = texture
                    container.colonies = self.imgRef.colonies
            
    def zoom_in(self):
        if self.scale < 10:
            self.apply_transform(Matrix().scale(1.2, 1.2, 1.2), anchor=self.parent.center )
    
    def zoom_out(self):
        if self.scale > 1:
            self.apply_transform(Matrix().scale(1/1.2, 1/1.2, 1/1.2), anchor=self.parent.center )

    # Swap image with processed image and back
    def swap_image(self):
        global swap

        if (swap == 0):
            self.ids.relativeContainer.clear_widgets()
            self.replace = AsyncImage(texture = self.imgRef.texture, size = (self.parent.width, self.parent.height) )
            self.ids.relativeContainer.add_widget(self.replace)
        else:
            self.ids.relativeContainer.clear_widgets()
            self.replace = AsyncImage(source = self.imgRef.source, size = (self.parent.width, self.parent.height))
            self.ids.relativeContainer.add_widget(self.replace)

    # Set image back to it's original size and position
    def reset_image(self):
        self.scale = 1
        self.pos = self.parent.pos


class InfoContainer(BoxLayout):
    tools_visible = BooleanProperty(False)
    toggle_state = BooleanProperty(True)
    fullscreen_mode = BooleanProperty(False)

    def toggle_tools(self):
        self.tools_visible = not self.tools_visible
        self.update_ui_based_on_tools_visibility()

    def update_ui_based_on_tools_visibility(self):
        
        if self.tools_visible:
            # Hide the edit button
            self.ids.edit_button.size_hint = (None, None)
            self.ids.edit_button.size = (0, 0)
            self.ids.edit_button.opacity = 0

            self.ids.colonies_detected_section.size_hint = (1, 0.038)

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
        app = App.get_running_app()
        app.root.ids.prevContainer.add_mode = not app.root.ids.prevContainer.add_mode
        app.root.ids.prevContainer.remove_mode = False
    
    def remove_colony(self):
        app = App.get_running_app()
        app.root.ids.prevContainer.remove_mode = not app.root.ids.prevContainer.remove_mode
        app.root.ids.prevContainer.add_mode = False
    
    def zoom_in(self):
        print("Zoom In was pressed")


    def zoom_out(self):
        print("Zoom Out was pressed")
    
    def full_screen(self):
        # Get the current running app instance
        app = App.get_running_app()
        self.fullscreen_mode = not self.fullscreen_mode
        # Assuming the root widget is MyGridLayout or has an attribute to access it
        if self.fullscreen_mode:
            print("Full Screen was pressed")
            self.size_hint = (None, 1)
            self.ids.spacer_under_infocontainer.size_hint_y = 0.092
        else:
            print("Exit Full Screen was pressed")
            self.size_hint = (0.4, 0.1)
            self.ids.spacer_under_infocontainer.size_hint_y = 0.01

        if hasattr(app, 'root'):
            my_grid_layout = app.root  # or however you can access MyGridLayout from app
            my_grid_layout.toggle_fullscreen()
        else:
            print("MyGridLayout instance not found")

    
    def switch_toggle(self):
        self.toggle_state = not self.toggle_state
        print("Toggle button was pressed, state is now:", "On" if self.toggle_state else "Off")
    
    
    def remove(self):
        self.parent.remove_widget(self)



class MyGridLayout(Widget):
    fullscreen_mode = BooleanProperty(False)  # Track fullscreen mode state

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
            imageContainer = ImageContainerWidget(source = file_path, texture = None, numpy_image = None, colonies = None)
            imageContainers.append(imageContainer)
            self.ids.image_box.add_widget(imageContainer)

            # Set a reference to this MyGridLayout instance on the new ImageContainerWidget
            imageContainer.my_grid_layout = self

            for container in imageContainers[:-1]:  # Exclude the last one, which is the newly added
                container.is_selected = False

            # Select the last added image
            imageContainers[-1].is_selected = True 

            self.ids.prevContainer.imgRef = imageContainers[-1]
            self.ids.prevContainer.ids.previewer.source = file_path
            if (self.ids.prevContainer.replace != None):
                self.ids.prevContainer.replace.source = file_path

            self.ids.prevContainer.ids.previewer.opacity = 1
            print(imageContainers)
        else:
            print("Could not open")
    
    # Update Image in the image previewer
    def previewer_update(self, imgReference):
        global swap

        container = self.ids.prevContainer
        container.reset_image()
        container.imgRef = imgReference

        if (imgReference.colonies is not None):
            self.infoContainer.ids.colony_count_text.text = str(len(imgReference.colonies[0]))
        if (container.replace == None):
            container.ids.previewer.source = imgReference.source
        else:
            if(swap == 1):
                container.replace.source = imgReference.source
            else:
                container.replace.texture = imgReference.texture

    def activate_cancel(self):
        self.ids.process_button.text = "Process"
        self.ids.upload_button.text = "Upload"
        self.processing = True
        self.infoContainer.remove()

    def convert_to_texture(self, image):
        w, h, _ = image.shape
        texture = Texture.create(size=(h, w))
        texture.blit_buffer(image.flatten(), colorfmt='rgb', bufferfmt='ubyte')

        return texture
    
    def start_processing(self):
        print("Processing started...")

        for container in imageContainers:
            if(container.texture == None):
                colonies, numpyImage = process_images_from_paths([container.source])
                if colonies[0] is not None:
                    container.texture = self.convert_to_texture(annotate_image(np.copy(numpyImage[0]), colonies[0]))
                else:
                    container.texture = self.convert_to_texture(numpyImage[0])
                container.numpy_image = numpyImage
                if colonies[0] is not None:
                    container.colonies = colonies[0]
                else: 
                    # Create empty colonies array when 0 colonies detected
                    container.colonies = np.uint16(np.empty((1,0,3)))

        if (len(imageContainers) != 0):
            self.infoContainer = InfoContainer()
            self.ids.right_side_layout.add_widget(self.infoContainer)
            self.infoContainer.ids.colony_count_text.text = str(len(self.ids.prevContainer.imgRef.colonies[0]))

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

    def toggle_fullscreen(self):
        self.fullscreen_mode = not self.fullscreen_mode
        # app = App.get_running_app()
        # info_container = app.root.ids.info_container

        if self.fullscreen_mode:
            # Enter fullscreen mode

            self.ids.image_scroll_view.size_hint = (0, 0)  # Hide image list
            self.ids.upload_process_container.size_hint = (0,0)
            self.ids.upload_button.opacity = 0
            self.ids.upload_button.text = ""
            self.ids.process_button.opacity = 0
            self.ids.process_button.text = ""
            self.ids.prevContainer.reset_image()
            
        else:
            # Exit fullscreen mode, restore original layout
            self.ids.image_scroll_view.size_hint = (0.4, 1)
            self.ids.upload_process_container.size_hint = (1,0.3)
            self.ids.upload_button.opacity = 1
            self.ids.upload_button.text = "Cancel"
            self.ids.process_button.opacity = 1
            self.ids.process_button.text = "Export"

            self.ids.prevContainer.reset_image()


    
    # Toggle images between processed and non-processed versions
    def toggle_images(self):
        global swap
        if (swap == 0):
            swap = 1
        else:
            swap = 0

        for container in imageContainers:
            container.swap_image()
        
        # Toggle image in container to unprocessed/processed
        self.ids.prevContainer.swap_image()

# buttons in tools section
class ImageButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(ImageButton, self).__init__(**kwargs)
        self.hovered = False  # Attribute to track hover state
        Window.bind(mouse_pos=self.on_mouse_pos)  # Bind to mouse position changes

    # this function called whenever the mouse position changes
    def on_mouse_pos(self, *args):
        pos = args[1]  # args[1] is the mouse position
        inside = self.collide_point(*self.to_widget(*pos))  # Check if mouse is inside the widget
        if inside:
            if not self.hovered:  # Check if hover state needs to be updated
                self.hovered = True
                self.on_cursor_enter()
        else:
            if self.hovered:
                self.hovered = False
                self.on_cursor_leave()

    def on_cursor_enter(self):
        # print("cursor on")
        Window.set_system_cursor('hand')

    def on_cursor_leave(self):
        # print("cursor off")
        Window.set_system_cursor('arrow')

    def on_press(self):
        super(ImageButton, self).on_press()
        # Temporarily change the color tint to indicate a highlight
        self.color = (0.1, 0.8, 0.8, 1)
        Clock.schedule_once(self.remove_highlight, 0.3)

    def remove_highlight(self, *args):
        # Revert to the original color tint
        self.color = (1, 1, 1, 1)

    def on_parent(self, instance, value):
        # Unbind from mouse_pos when the widget is removed from its parent
        if value is None:
            Window.unbind(mouse_pos=self.on_mouse_pos)

class DefaultButton(ButtonBehavior, Label):
    def __init__(self, **kwargs):
        super(DefaultButton, self).__init__(**kwargs)
        self.hovered = False  # Initialize the hovered attribute here
        Window.bind(mouse_pos=self.on_mouse_pos)  # Bind to mouse position changes

        # Default visual style
        self.font_size = 80
        self.size_hint = (1, 0.5)
        self.background_color = (0.5, 0.5, 0.5, 0)  # Makes the default button background transparent
        
        # Custom drawing instructions for the button
        with self.canvas.before:
            Color(rgba=(0.3, 0.3, 0.3, 1))  # Button color
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[30])
            self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_mouse_pos(self, *args):
        pos = args[1]  # args[1] is the mouse position
        inside = self.collide_point(*self.to_widget(*pos))  # Check if mouse is inside the widget
        if inside:
            if not self.hovered:  # Check if hover state needs to be updated
                self.hovered = True
                self.on_cursor_enter()
        else:
            if self.hovered:
                self.hovered = False
                self.on_cursor_leave()

    def on_cursor_enter(self):
        print("cursor on")
        Window.set_system_cursor('hand')

    def on_cursor_leave(self):
        print("cursor off")
        Window.set_system_cursor('arrow')

    def on_press(self):
        super(DefaultButton, self).on_press()
        # Temporarily change the color tint to indicate a highlight
        self.color = (0.1, 0.8, 0.8, 1)
        Clock.schedule_once(self.remove_highlight, 0.3)

    def remove_highlight(self, *args):
        self.color = (1, 1, 1, 1)

    def on_parent(self, instance, value):
        # Unbind from mouse_pos when the widget is removed from its parent
        if value is None:
            Window.unbind(mouse_pos=self.on_mouse_pos)

    




class CustomLayout(BoxLayout):
    pass


class colonyGUI(App):
    def build(self):
        self.myLayout = MyGridLayout()
        return self.myLayout
    
    
if __name__ == '__main__':
    colonyGUI().run()
