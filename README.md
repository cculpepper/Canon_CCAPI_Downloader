# Canon_CCAPI_Downloader
Python script to pull files from a CCAPI enabled camera automatically, while the camera is in use. 

I'm using this with a Canon EOS RP connected to WIFI. IT seems to work pretty well. I'd set this up to run every 5 minutes or so.

While files are being downloaded, the camera can still be used, however it can hang for a second if the web request gets there first.

If you start shooting in the middle of a download, the download will fail eventually, and will be retried after 5 seconds. 

Change the first few lines in the puller.py to match your setup.
