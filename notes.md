# Bond Grapher

## graph report
--- NODES ---
ID: 0, Label: "SF", Type: node, Pos: (359, 242)
ID: 1, Label: "C", Type: node, Pos: (410, 394)
ID: 2, Label: "R", Type: node, Pos: (591, 550)
ID: 3, Label: "I", Type: node, Pos: (870, 550)
ID: 4, Label: "0", Type: junction, Pos: (539, 318)
ID: 5, Label: "1", Type: junction, Pos: (734, 387)

--- EDGES ---
"SF" -> "0" (Label: 1)
"0" -> "C" (Label: 2)
"0" -> "1" (Label: 3)
"1" -> "R" (Label: 4)
"1" -> "I" (Label: 5)

## TODO updates for Tkinter graph GUI program
- [x] Add functionality to save and load graphs from files.
- [x] Implement zooming and panning features for better navigation.
- [x] Add a feature to export the graph as an image (PNG)
- [x] add status bar to display information about the current tool, selected node/edge, etc.
- [x] stop using pop-ups for informing user , instead use status bar
- [x] change color of active button
- [x] implement multiple selection of nodes and edges
- [x] press delete key to delete selected nodes and edges
- [x] drag to select multiple nodes and edges
- [x] auto-populate edge name to next available number

- [ ] Add tooltips to nodes and edges to display additional information on hover.
- [ ] Implement undo and redo functionality for graph modifications.

- [ ] Report Button causes program to run