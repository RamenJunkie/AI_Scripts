# Libation Helper Scripts

These are a couple of scripts to assist with audiobooks and Libation.  Maybe there  is a way to do some of this in the software but I found it a bit cumbersome and unintuitive to use outside it's basic purpose.

Both scripts require an up to  date library export file in JSON format, renamed to books.json.

- filterbooks.py will output a text file "not_liberated_books.txt" in Author - Book format of any book not "liberarted".  It filters out anything that is an "Episode" (Podcasts).
- audiobook_organizer.py will sort and move all downloaded folders in BookTitle[ID] folder format into folders based on author, Author/BookTitle[ID].
