### Unix-Launcher Release Place
Unix Launcher is an experiment, is it possible to make a good well-designed minecraft launcher in python only?
Check out our discord! [Discord](https://discord.gg/BVpWyqr8E3) (all news here)
If you found any bugs, write them in issues or join our discord server, go to the `support` category, create a new ticket and describe the bug you found (discord server is for Russians only, don't worry, we have English chat and we will translate your problem for you).
#### Please, note that this is a **main** branch and source files here for the **release version**.
---
#### How to launch
1. Open terminal in ulauncher folder.
2. Type into command prompt: pip install -r requirements.txt
3. And you're done! You have installed all libraries now you can run source code or build it.
---
#### How to build an exe app
1. **Install all libraries**
Open the ulauncher folder in it open a terminal and move to the ulauncher directory or it will automatically be on the path of the ulauncher folder then also write in the terminal this: pip install -r requirements.txt
---
2. **Build .py file into .exe file**
In order to do this you need to use third-party libraries to compile .py into an .exe file, I use Pyinstaller as an example, and you should too
Repeat the previous steps with terminal (open in ulauncher folder path) and write there: pyinstaller <your arguments e.g. --onefile, --noconsole> main.py
---
3. **You're done! Open `dist` folder and here's your .exe file!**
Just don't forget to move the assets folder into the folder along with the .exe file, otherwise assets for launcher won't be visible.
---
### Im getting viruses in my .exe file, why?
Answer [here](VirusesExplaination.md)
  
