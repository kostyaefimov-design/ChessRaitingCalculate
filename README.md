# Chess-Results Rating Calculator

A graphical interface application designed to automatically calculate chess rating changes after a tournament. The tool gathers data directly from chess-results.com and computes both the expected and actual match outcomes.

## Features

* **Automated Data Collection:** The script connects to the player's profile page, extracts their current rating, retrieves opponents' ratings, and logs the outcomes of finished matches.
* **Instant Calculation:** The application uses the standard Elo formula with a K-factor of 40 to quickly determine the exact points gained or lost.
* **Graphical Interface:** The application includes a dark theme, a simple text field for the URL, and a clear visual presentation of the results with color-coded rating changes.

## Requirements

You need Python 3.7 or a newer version to run this application. You also need to install a few third-party libraries for the graphical interface and web scraping.

Required packages:
* flet
* requests
* beautifulsoup4

## Installation

Clone the repository to your local machine and open the project directory.

Install the required packages using pip:

```bash
pip install flet requests beautifulsoup4
```
## Usage
Launch the application to open the main window. Copy the URL of a specific player's result page from an ongoing or finished tournament on chess-results.com. Paste the link into the input field and click the calculate button. The application will process the data and display the initial rating, the number of games played, the new expected rating, and the total point difference.
