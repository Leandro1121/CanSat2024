from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window

Window.size = (300, 200)


class MainWindow(BoxLayout):
    def __init__(self):
        super().__init__()
        self.button = Button(text="Hello, World?")
        self.button.bind(on_press=self.handle_button_clicked)

        #self.add_widget(button)

    def handle_button_clicked(self, event):
        self.button.text = "Hello, World!"


class MyApp(App):
    def build(self):
        self.title = "Hello, World!"
        return MainWindow()


app = MyApp()
app.run()