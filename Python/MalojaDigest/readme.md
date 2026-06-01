# Maloja Weekly Digest to Joplin

Uses the Maloja API to pull a weekly list of top 5 Arts, Albums, and Songs, as well as a list of everything played, and stores it in both a local MArkdown file and writes it to a Joplin Notebook.  Joplin CLI must be installed on the system running the script.

By default it collects 1 week worth of data based on running the script on a cron job cycle.

The backfill script will create markdown files for all previous weeks through Feb 2005.  Dates could be adjusted int he code if more are needed, that was just, all I needed.  Blank weeks are skipped.  It does not import the files to Joplin though that could be done manually.

[Maloja](https://github.com/krateng/maloja) is a self hosted Last.fm solution.
