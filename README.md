# Drive2CloudSync
## _A Real-Debrid Quasi-Clone Media Library Curator_

Drive2CloudSync is a Python script designed to help real-debrid cloud service users efficiently organize and maintain a highly structured, portable media collection on a remote drive. By iterating through folders within [rclone_RD] mounted drive containing user's remote downloaded torrents, Drive2CloudSync identifies whether each folder contains a movie or a TV show. It then leverages the python-torrent-title (PTN) library (version 2.5) to parse the torrent name and extract relevant media information. Based on this information, the script organizes a folder hierarchy on a user-specified drive location and populates it with .strm files containing links to the media resources.

## Table of Contents
1. [Features](#features)
2. [Usage](#usage)
3. [Configuration](#configuration)
4. [Scheduled Task](#scheduled-task)
5. [Plugins](#plugins)
5. [Contributing](#contributing)
6. [License](#license)


## Features
Drive2CloudSync offers several features to enhance your media organization and access experience:

- **Media Detection:** Automatically identifies whether a folder contains a movie or a TV show.
- **Metadata Extraction:** Utilizes the PTN library to extract metadata from folder names.
- **Structured Hierarchy:** Creates a well-structured folder hierarchy based on media information.
.strm Files: Generates .strm files with renewed links every 7 days to ensure continuous access.
- **Compatibility:** Works seamlessly with Kodi, Plex, Emby, and similar media players.
- **Low-Powered Device Access:** Allows users to access their cloud media collection on low-powered devices.
- **Portability:** The portable quasi-clone can be easily mounted on different devices.

## Usage
Before you can use Drive2CloudSync, you'll need to install Python (version >3.10) and ensure you have the necessary dependencies. Follow these steps to get started:
1. Clone this repository to your local machine:
    ```sh
    git clone https://github.com/honest-mule/Drive2CloudSync.git
    ```
2. Navigate to the project directory:
    ```sh
    cd Drive2CloudSync
    ```
3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```
3. Make a copy of `settings.example.py` file:
    ```sh
    cp settings.example.py settings.py
    ```
4. Edit and add appropriate API keys in `settings.py` file
5. Edit source and destination paths in `settings.py` file
6. Run the script by using the following command:
    ```sh
    python cataloguer.py
    ```
7. Monitor `status.log` file for info, errors & exceptions

## Configuration
Drive2CloudSync allows for some customization through its configuration file. To configure the script to your preferences, follow these steps:

Open the `settings.py` file in the project directory.

Modify the following settings as needed:

`SOURCE_DRIVE`: The path to your debrid cloud folder containing downloaded torrents.
`DEST_ROOT`: The destination drive location where the nicely-named sophisticatedly structured hierarchy will be created.
`FOLDER_CHECK_FREQUENCY`: Amount of time after which the rclone_RD mounted drive should be checked for changes
Save your changes.
`RENEW_ALL_LINKS_AT`: The daily hour after which the whole rclone_RD mounted drive should be re-iterated for dead-links

## Scheduled Task
For convenience, consider setting up a scheduled task (e.g., using cron on Unix-like systems) to run Drive2CloudSync at your preferred event. This ensures your media collection remains updated without manual intervention.

Example for running Drive2CloudSync at every reboot:
`@reboot /usr/bin/python /path/to/drive2cloudsync/cataloguer.py`

## Plugins

Drive2CloudSync is currently dependent on the following projects.
Instructions on how to use them are linked below.

| Plugin | README |
| ------ | ------ |
| Rclone_RD | [rclone_RD/README.md][rclone_readme] |

## Contributing
If you'd like to contribute to this project, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with clear, concise commit messages.
4. Push your changes to your fork.
5. Create a pull request with a detailed description of your changes.

Your pull request will be reviewed, and your contributions are greatly appreciated!

## License
This project is licensed under the [MIT License]. Feel free to use, modify, and distribute it according to the terms of the license.

   [rclone_RD]: <https://github.com/itsToggle/rclone_RD>
   [rclone_readme]: <https://github.com/itsToggle/rclone_RD/blob/master/README.md>
   [MIT License]: <https://mit-license.org/>
