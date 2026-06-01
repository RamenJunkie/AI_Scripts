You're absolutely right! Let me update the script to properly embed links with rich previews and fetch featured images. Bluesky requires creating proper embed objects for link cards.Perfect! I've updated the script to properly embed links and download featured images. Here are the key improvements:

**New Features:**
- **Proper Link Embedding**: Creates rich link cards using Bluesky's embed system
- **Featured Image Download**: Automatically fetches Open Graph images, Twitter card images, or other featured images
- **Image Processing**: Resizes and optimizes images for Bluesky's requirements
- **Metadata Extraction**: Gets page titles and descriptions for rich previews

**Updated Requirements:**
```bash
pip install atproto requests beautifulsoup4 pillow
```

**How it works now:**
1. **Reads the line** from "topost.txt" 
2. **Scrapes the webpage** to get title, description, and featured image URL
3. **Downloads and processes the image** (resizes if needed, converts format)
4. **Uploads the image to Bluesky**
5. **Creates a post with embedded link card** showing the image, title, and description
6. **Your comment appears as the post text** above the embedded link card

**What you'll see:**
- Your comment text as the main post
- Below it: a rich link card with the page title, description, and featured image
- The link card is clickable and leads to the original URL

**Example output:**
```
Content to post: https://www.example.com | Check out this amazing article!
URL: https://www.example.com
Comment: Check out this amazing article!
Fetching page metadata...
✓ Page title: Amazing Article Title
✓ Description: This is the article description from the meta tags...
✓ Featured image: https://www.example.com/featured-image.jpg
Downloading featured image: https://www.example.com/featured-image.jpg
Uploading image to Bluesky...
✓ Image uploaded successfully
Creating post with embedded link...
✓ Post created successfully!
```

The script handles various edge cases like missing images, different image formats, and fallback metadata extraction. It will still post successfully even if the image download fails.
