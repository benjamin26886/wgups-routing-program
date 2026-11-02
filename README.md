# WGUPS Routing Program

A Python delivery-routing program for the WGU C950 (Data Structures and Algorithms II) project. It schedules 40 packages across three trucks in Salt Lake City, aiming for a combined route under 140 miles while meeting each package's deadline and special notes.

## Features
- **Custom hash table** (separate chaining) for storing and looking up packages. It's written from scratch and doesn't use Python's `dict`.
- **Nearest Neighbor** routing for each truck.
- **Interactive menu** to check one package or all packages at any time of day, and to see the total mileage.

## Project structure
| File | Description |
|------|-------------|
| `main.py` | Main program: hash table, data loading, routing, menu |
| `packages.csv` | Package data |
| `distances.csv` | Address list and distance matrix |
| `tools/` | Helper scripts for rendering screenshots and building the report |
| `screenshots/` | Program output at 9:00, 10:00, and 12:15, plus total mileage |
| `Final_Report.md`, `*.docx`, `*.pdf`, `*.html` | Written project reports |

## Running
Requires Python 3 (standard library only).

```bash
python3 main.py
```
