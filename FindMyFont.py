"""
Purpose: Find a free font alternative to a purchasable font.

It uses Google Fonts to get fonts from its database, and compares the user's given font
to the others in the database. After completion, the fonts are displayed along with a difference percentage. 
The smaller the difference percentage, the better the fonts match. i.e., 0% means its an exact match.

Currently, it only works with .ttf files and will ignore .otf 

Summary:
    - Uses a simple api request to get the fonts sorted by popularity
    - Converts the .ttf file type into a shapely polygon object
    - Compares both shapely polygons and finds the difference, storing the top matches in a scoreboard
    - The lower the difference percentage, the better the match is
"""

from urllib.request import urlopen
import urllib.request
import json
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from svgpath2mpl import parse_path as mpl_parse_path
from shapely.geometry import Polygon
import shapely.affinity as affinity
import constants


"""
These are the settings that can be changed to find the alternative. 

    location1: can be changed to link to the purchaseable font that we are finding an alternative to.
        Note that it must be locally stored on the computer
        
    local_font2 & location2: an extra feature that checks two local fonts and compares them for similarity.
        Leave local_font2 = False as is if you wish to find a match within Google Fonts database
        
    lower_bound & upper_bound: Corresponds to the range of fonts in the Google Fonts database.
        We limit the search so it doesn't waste time going through the entire database since the
        best matches tend to happen between ranges 1-50 and 1-100
        
    check_chars: These are the characters we will use to find the free alternative.
        Enter the most unique characters for the best match
    
"""
###SETTINGS###

# Location 1 is the local font we match to the database. Enter the location of the .ttf file you 
# wish to find a free alternative to 
location1 ="./Fonts Demo/Lato-Regular.ttf"

# Gets the api key from constants.py
API_KEY = constants.API_KEY

# Flag for comparing two local fonts for similarity
local_font2 = False
location2 = "./Fonts Demo/Lato-Regular.ttf"

# Corresponds to the range of fonts in the database to search through. 
# This searches the first 1-50 fonts.
lower_bound = 1
upper_bound = 50

# These are the characters we will match up to find the free alternative
check_chars = ['A','B','C']

# Initialize ranking scoreboard at the worse possible percentage of difference.
# i.e. 100 corresponds to the two not overlapping at all
ranking=[[100,""],[100,""],[100,""],[100,""],[100,""]]

#########

"""
Checks and updates the scoreboard.
"""
def addScore(array, score, url):
    j=0
    i=0
    # Check throughout the entire array
    for i in range(array.__len__()):
        # Stop when our new value is better than the one stored
        if score <= array[i][0]:
            j=array.__len__()-1
            break
    # Shift all elements down to fit our new score
    while j > i:
        array[j][0] = array[j-1][0]
        array[j][1] = array[j-1][1]
        j = j-1
    # Store the new score
    if score <=array[i][0]:
        array[i][0] = score
        array[i][1] = url   
    
"""
Takes a fonttools TTFont object and converts it to a shapely Polygon
If the font has extra shapes this combines them together all into one object.

Note: the holes in letters will essentially be erased.
Ex. in the letter 'o' ttfont2poly will erase the inner ring, and only use the 
outer ring for comparison.
"""
def ttfont2poly(font, letter):
    # Get the glyphset to see the letters
    glyph_set = font.getGlyphSet()
    
    # Get the specific letter from the glyph set
    glyph = font['glyf'][letter]
    
    # Convet glyph to an svg
    svg = SVGPathPen(None)
    glyph.draw(svg, glyph_set)
    
    # Parse the svg into a path that Shapely can read using matplotlib
    mpl_path = mpl_parse_path(svg.getCommands())
    coords = mpl_path.to_polygons()
    
    # Union all shapes together, since some fonts have seperate strokes that we want to include
    poly = Polygon(coords[0])
    for i in range(coords.__len__()):         
        poly = poly.union(Polygon(coords[i]))
    return poly

"""
Calculates the x and y lengths of the bounding box enclosing the Polygon letter
"""
def getPolyFactor(poly):
    x = poly.bounds[2]- poly.bounds[0]
    y = poly.bounds[3] - poly.bounds[1]
    
    return (x,y)

"""
Calls functions to perform the differnce percentage comparison.

This will also scale the fonts in the database, so the bounding boxes match the 
first font. This is done in case the fonts are different font sizes, so this way 
we get a fair comparison

    total stores the total average for every letter we used to match
    count stores the number of letters
    total/count gives us the overall percentage difference
"""
def match(check_chars, location1, location2):
    # Initialize variables
    total = 0 # Stores the difference area of all letters
    count = 0 # Used to calculate the average percentage
    
    # Load the fonts as a TTFont object
    font1 =TTFont(location1, lazy=False)
    font2 = TTFont(location2, lazy=False)
   
    # Perfom conversions and calculations on each letter the user wishes to match
    for i in check_chars:
        count = count+1
        # Convert the fonts to 
        poly1 = ttfont2poly(font1, i)
        poly2 = ttfont2poly(font2, i)
      
        # Get factors to scale 2nd poly to first, so the sizes are the same for a fair comparison
        x1,y1 = getPolyFactor(poly1)
        x2,y2= getPolyFactor(poly2)
        scale_poly2 = affinity.scale(poly2, xfact=(x1/x2), yfact=(y1/y2), origin=(0,0))
        
        # Calculate the intersection and union
        intersection = poly1.intersection(scale_poly2)
        union = poly1.union(scale_poly2)
               
        # Calculates the difference, and divides by union to get the percentage of 
        # difference for a single letter, and adds it to total to account for multiple letters
        total += (union.area - intersection.area)/union.area
    # Calculates the overall average by divding the total number of difference
    #  averages by the number of letters we used to compare
    return (total/count)

"""
Formats and prints the ranking scoreboard
"""
def printScore(array):
    print("\nYour Fonts are here:")
    for i in range(array.__len__()):
        print(f"{i+1}.  Difference: {array[i][0]:.2f}%\n\t{array[i][1]}")
    pass
 
""""
Part of program that makes the api call, and function calls


"""
####### MAIN #######

# If user is providing us with two local fonts to compare, simply print out the number
if local_font2 == True:
    try:
        print(f"Difference: {match(check_chars, location1, location2):.2f}%")
    except:
        print("Something went wrong. Also remember this only works for .ttf file types")
else:        
    # We will lookup the closest matching font in the Google Fonts database
    
    # Get the fonts sorted by popularity
    url = f"https://www.googleapis.com/webfonts/v1/webfonts?key={API_KEY}&sort=popularity"

    # Get the json response
    response = urlopen(url)

    # Store JSON from url into data
    data = json.loads(response.read())
    
    # Get the user's font that we will find an alternative to
    try:
        font1 = open(location1, "r")
    except:
        print("Could not find font")
        
    # Iterate through range of fonts we want to search
    for fonts in range(lower_bound, upper_bound):
        # retrieve font2 from the api
        font_URL = data['items'][fonts]['files']['regular']
        
        # Get the second font frorm the api request
        location2 = urllib.request.urlretrieve(font_URL)
        # Print so the user can see which fonts it's looking through
        print(font_URL) 
        
        # Get the score and add the score the ranking scoreboard
        try:
            score = match(check_chars, location1, location2[0])
            addScore(ranking, score*100, font_URL)
            
        except: # Skips .otf files, or if theres an error with files
            pass
    # Print the ranking scoreboard
    printScore(ranking)
  
