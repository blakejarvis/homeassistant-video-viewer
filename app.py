from flask import Flask, render_template, send_from_directory, request
import os
from os import walk
import shutil
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    # Figure out if content is wanted for today or another day
    date_requested = request.args.get('date')
    if date_requested is None:
        # Default to serving today's videos
        today = datetime.today().strftime('%Y-%m-%d')
    else:
        today = date_requested


    # Set directory of date selected's videos
    # Remove dot if using Docker, add dot and ln -s uploads to FTP path if testing locally
    original_today_videos_dir = os.path.join('/uploads',today) 
    
    # If the requested directory doesn't exist in the file system, return no videos
    if not os.path.isdir(original_today_videos_dir):
        # Retrun execution flow
        return render_template('index.html', video_list=[], date=today, message="No videos on " + today)

    # If the app reaches this point in the code, the yyyy-mm-dd directory exists in the video filesystem
    
    # Make sure the today folder exists in the flask app
    today_folder = os.path.join("static","videos",today)
    today_folder_exist = os.path.isdir(today_folder)
    if not today_folder_exist:
        os.makedirs(today_folder)

    # Get all file names in the original file location by recursively going into directories
    files = {}
    # files = {"file1.mp4": "17hour", "file2.mp4": "18hour" }

    # Iterate through the files in the directory, add their name and hour to dict
    for dirpath, dirs, data_files in os.walk(original_today_videos_dir):
        if data_files is not []:
            for item in data_files:
                if item.endswith(".mp4"):
                    hour = dirpath.rsplit('/',2)[1] # Returns 17hour (no dav)
                    files[item] = hour
            
    # Sync the remaining mp4's with the /videos/yyyy-mm-dd/[file].mp4 directory
    # Could definitely optimize this here by first checking if the file has previously been copied
    # Also add to a new array the flask/docker-relevant file path locations
    video_list = []
    for video_name,hour in files.items():
        shutil.copy(os.path.join(original_today_videos_dir,hour,"dav",video_name),os.path.join(today_folder,video_name))
        video_list.append(video_name)

    # Re-order the videos to be in most recent to least recent, going top-town
    video_list = sorted(video_list, reverse=True)

    # Set the HTML page title dynamically
    message = "Videos for " + today

    ######
    #
    # Scrolling
    #
    # Only return 3 videos at a time. This will speed up the app a lot.
    # And also evaluate if the user has "scrolled" 3 videos forward or back
    # The dataset is the video_list array
    #
    #####
    video_list_length = len(video_list)
    video_list_shortened = []    
    first_video = request.args.get("video_requested")

    if first_video is not None:
        first_video = int(first_video)

    # Use a warning string as a helpful error when scrolling
    warning = ""
    
    if first_video is None:
        # if no param is set, set first_video to 0, return the first 3 items
        first_video = 0
        video_list_shortened = video_list[0:3]

    elif video_list_length < 4:
        # elif there are 3 or less videos in the list, return the whole list
        video_list_shortened = video_list

    elif first_video > (video_list_length-3):
        # elif first_video is greater than total number of videos-3, set an error and return last 3 videos
        video_list_shortened = video_list[-3:]
        warning = "These are the oldest 3 videos of the day"

    elif first_video < 1:
        # elif first_video is less than total number of videos, set an error and return first 3 videos
        video_list_shortened = video_list[0:3]
        warning = "These are the newest 3 videos of the day"

        # Set the video index to be 3 to account for the -3 offset in the return statement below
        first_video = 3

    else:
        # Else, return the item selected, plus 3
        video_list_shortened = video_list[first_video:first_video+3]

        
    return render_template('index.html',
                           video_list=video_list_shortened,
                           date=today,
                           message=message,
                           warning=warning,
                           first_video=first_video-3,
                           last_video=first_video+3
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)
