- [X] Increase text input box to allow multiple lines, 10 lines.
- [X] Input text field for AI must be ingested and provide a list of identified actions under text box not directly make changes in vault like create a new thread, mark a task as complete... Indentified action must be placed in a Queque of actions pending aprobation or discard by user.  Example: promtpt(create main theads, BESS, PV) ->  Action1:  Create Level1 thread[BESS] [Discard][OK],  Action2:  Create Level1 thread[PV][Discard][OK]
- [X] Create icons in background, after the OK user, response for actions pending [Discard][OK] must be faster and not necesary the icon at this initial step of digestion prior to action of creation.
- [X] bug:  after prompt run in AI text box,  message "Thinking… interpreting your note and generating any new icon" not in concordance with previous features implemented.
- [X] bug: Nothing to do from “new thead DEV”. is a clear action, create a new Level 1 thread!
- [X] feat:  improve user feedback during keyboard navigation of selected position, now button are rounde by a blue line, sometimes beacause of background color is dificult to see.
- [X] bug:Also seems that ai input box is unreachable by keyboard.
- [X] feat:provide in input box some tips of commans templates, this tips disapear when user start typing
- [X] feat:  help button with a list of inputs examples that provide actions.
- [X] review: create a new specs_v11.md file with features an better UI.
- [X] feat:  for  upper left home shorcut where the name of app are in text,  create a icon for the app not only text.
- [X] git action: merge v1.0 branch to main. Do it [PS C:\_Dev\Python\Projects\focus-mode-on> git push origin main
  Total 0 (delta 0), reused 0 (delta 0), pack-reused 0 (from 0)
  To https://github.com/pchinso/focus-mode-on.git
  74ea046..107067d  main -> main
  PS C:\_Dev\Python\Projects\focus-mode-on>]
- [X] git action: new branch v1.1
- [X] feat: in branch v1.1 implement specs_v11.md features (done: Approve/Discard all, dashboard search, command palette Ctrl+K, rename task, delete task, responsive layout, HTML report export, regenerate icon, task reorder up/down, per-thread accent color, thread re-parent, edit-before-approve, archive undo toast)
- [X] feat : include how old are a task based on date of creation, this allows to find old task pendings.  example: Task 1(2h ago),  task 2(7 days ago)...
- [X] feat: a button inside Thread page to create a new one under this.
- [X] bug: button move allows click with any destination selected,  disable if any destination is selected.
- [X] feat: AI input text box allways visible, also under a thread page revision, ready to accept inputs.
- [X] bug: some icons in dark mode generated are invisible.
- [X] feat: under [Personal-Work mode1 thread[ ] [![img](http://127.0.0.1:8000/icon/personal/sport)SPORT **all done · 1 sub-thread**](http://127.0.0.1:8000/thread/personal/sport)] a llist of pending task panel visible by [+] button shows ordered from older to new pending task by thread, are linkable to navigate to thread of the task.
- [X] bug: list of pending task panel visible by [+] button shows ordered from older to new pending task by thread, are linkable to navigate to thread of the task. **Only works in Personal mode?!! check for both!**
- [X] feat:  improve app, Responsiveness, [Make this app fully responsive and adaptive for multiple screen sizes and devices, including mobile phones, tablets, laptops, desktops, and large displays. Ensure that the layout automatically adjusts to different resolutions and orientations without breaking the design. Use flexible grids, scalable components, responsive typography, proper spacing, and adaptive navigation.The app should provide a smooth and consistent user experience across all screen formats. Avoid fixed widths when possible, prevent overflow issues, and make sure buttons, menus, forms, images, and content remain clear, usable, and accessible on every device. Optimize the UI for both touch and mouse interactions, and follow modern responsive design best practices.]
