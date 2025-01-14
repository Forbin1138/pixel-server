from rpi_ws281x import PixelStrip, Color
import _rpi_ws281x as ws
from pixelconfig import PixelConfig
from flask import json
import re
import math
import random


# Defines the sequences available for pixelserver
# To add more entries create the new method in PixelSeq
# then update SeqList.pixel_sequences and PixelSeq.seq_methods.

# Sequence methods follow same format as arduino-pixels except
# no need for num_colors as that can be determined from colors list length



class SeqList():
    def __init__ (self):
        self.pixel_sequences = [
            {"seq_name" :"alloff",
             "title": "All Off",
             "description" : "Turn all LEDs off",
             "group" : 0
             },
            {"seq_name" :"allon",
             "title": "All On",
             "description" : "Turn all LEDs on",
             "group" : 0
             },
            {"seq_name" :"random",
             "title": "Random",
             "description" : "Random sequences",
             "group" : 0
             },
            {"seq_name" :"flash",
             "title": "Flash",
             "description" : "Flash all LEDs on and off",
             "group" : 0
             },
            {"seq_name" :"chaser",
             "title": "Chaser",
             "description" : "Flash all LEDs on and off",
             "group" : 0
             },
             {"seq_name" :"chaserchangecolor",
             "title": "Chaser Change Color",
             "description" : "Flash all LEDs on and off",
             "group" : 1
             },
             {"seq_name" :"chaserbackground",
             "title": "Chaser Solid Background",
             "description" : "Chaser sequence one block of colour across black background",
             "group" : 1
             },
             {"seq_name" :"chaserfillend",
             "title": "Chaser Fill End",
             "description" : "Single LED chaser to end and then fill up",
             "group" : 1
             }
            ]
        # default colors (can use any color, but these are default for chooing from)
        # used by random
        self.def_colors = [
                Color(255,255,255),
                Color(32,32,32),
                Color(255,0,0),
                Color(255,192,203),
                Color(0,128,0),
                Color(75,277,90),
                Color(0,0,255),
                Color(0,255,255),
                Color(192,0,192),
                Color(255,165,0),
                Color(0,0,0)
            ]
            
    # Return list of sequences in json format      
    def json (self):
        sequences = []
        for this_seq in self.pixel_sequences:
            sequences.append({
                "seq_name": this_seq["seq_name"],
                 "title": this_seq["title"],
                 "description": this_seq["description"],
                 "group": str(this_seq["group"])
                 })
        return json.jsonify(sequences)
    
    # returns true if valid sequence, otherwise false
    def validate_sequence (self, supplied_seq_name):
        for this_seq in self.pixel_sequences:
            if this_seq["seq_name"] == supplied_seq_name:
                return True
        return False
    
    # Include some color handling methods 
    # Check for valid color string - simple pattern matching ONLY
    def validate_color_string (self, color_string):
        pattern = r'[0-9a-f,]*'
        result = re.fullmatch(pattern, color_string)
        if result:
            return True
        else:
            return False
    
    def string_to_colors(self, color_string):
        # split based on , - assumes no # in string
        return_list = []
        parts = color_string.split(",")
        for this_part in parts:
            rgb = self.hex_to_rgb("#"+this_part)
            return_list.append(Color(*rgb))
        return return_list
    
    def hex_to_rgb(self, hx, hsl=False):
        """Converts a HEX code into RGB or HSL.
        Args:
            hx (str): Takes both short as well as long HEX codes.
            hsl (bool): Converts the given HEX code into HSL value if True.
        Return:
            Tuple of length 3 consisting of either int or float values.
            If not valid return white (255,255,255)
            """
        if re.compile(r'#[a-fA-F0-9]{3}(?:[a-fA-F0-9]{3})?$').match(hx):
            div = 255.0 if hsl else 0
            if len(hx) <= 4:
                return tuple(int(hx[i]*2, 16) / div if div else
                             int(hx[i]*2, 16) for i in (1, 2, 3))
            return tuple(int(hx[i:i+2], 16) / div if div else
                         int(hx[i:i+2], 16) for i in (1, 3, 5))
        else :
            return (255,255,255)
    


class PixelSeq():
    
    
    def __init__ (self, pixel_config):
        self.pixel_config = pixel_config
        self.seq_list = SeqList()
        # Used by randSeq method for tracking sequence
        self.randseq = ""
        self.randcolors = []
        
        self.seq_methods = {
            'alloff' : self.allOff,
            'allon' : self.allOn,
            'random' : self.randomSeq,
            'flash' : self.flash,
            'chaser' : self.chaser,
            'chaserchangecolor' : self.chaserChangeColor,
            'chaserbackground' : self.chaserBackground,
            'chaserfillend' : self.chaserFillEnd
            }
        
        self.strip = PixelStrip (
            pixel_config.ledcount,
            pixel_config.gpiopin,
            pixel_config.ledfreq,
            pixel_config.leddma,
            pixel_config.ledinvert,
            pixel_config.ledmaxbrightness,
            pixel_config.ledchannel
            )
        self.strip.begin()
        # During startup turn all LEDs off
        self.allOff (0, 0, [0])
        
    def updateSeq (self, seq_name, seq_position, reverse, colors):
        return self.seq_methods[seq_name](seq_position, reverse, colors)
    
    def allOff(self, seq_position, reverse, colors):
        for i in range (0, self.strip.numPixels()):
            self.strip.setPixelColor (i, Color(0,0,0))
        self.strip.show()
        # increment seq_position (used to detect full seq complete)
        seq_position += 1
        # max seq_position is how long sequence lasts
        if seq_position > 10:
            seq_position = 0
        return seq_position
    
    def allOn(self, seq_position, reverse, colors):
        color_pos = 0
        # if reverse then need color to start at far end
        if (reverse):
            color_pos = (self.strip.numPixels() % len(colors)) -1
        if color_pos < 0:
            color_pos = len(colors) - 1
        for i in range (0, self.strip.numPixels()):
            self.strip.setPixelColor(i, colors[color_pos])
            color_pos = self._color_inc (color_pos, len(colors), reverse)
        self.strip.show()
        # increment seq_position (used to detect full seq complete)
        seq_position += 1
        # max seq_position is how long sequence lasts
        if seq_position > 20:
            seq_position = 0
        return seq_position

    def flash(self, seq_position, reverse, colors):
        color_pos = 0
        # if reverse then need color to start at far end
        if (reverse):
            color_pos = (self.strip.numPixels() % len(colors)) -1
        if color_pos < 0:
            color_pos = len(colors) - 1
        for i in range (0, self.strip.numPixels()):
            # If flash off then set to off
            if (seq_position % 2 == 1) :
                self.strip.setPixelColor(i, Color(0,0,0))
            else:
                self.strip.setPixelColor(i, colors[color_pos])
                color_pos = self._color_inc (color_pos, len(colors), reverse)
        self.strip.show()
        seq_position += 1
        if (seq_position > 20) :
            seq_position = 0
        return seq_position

    # Chaser - moves LEDs to left or right
    # Only uses colours specified unless only one color in which case use second as black
    # Colors in order passed to it (starting from first pixel)
    # forward direction is moving away from first pixel
    # reverse direction moves towards first pixel
    def chaser(self, seq_position, reverse, colors):
        chase_colors = colors.copy()
        if (len(chase_colors) < 2) :
            chase_colors.append(Color(0,0,0))
            
        # seq_position indicates where to start in colors array
        color_pos = seq_position
        for i in range (0, self.strip.numPixels()):
            # if past last color then reset to 0
            if (color_pos >= len(chase_colors)):
                color_pos = 0
            self.strip.setPixelColor(i, chase_colors[color_pos])
            color_pos += 1
        self.strip.show()
        if (reverse == False):
            return self._seq_dec (seq_position, len(chase_colors)-1)
        else:
            return self._seq_inc (seq_position, len(chase_colors)-1)
        
        
    # Chaser using only a single color at a time
    # shows 4 LEDs on by 4 LEDs off
    # If number of pixels is divisible by 8 then change on single block
    # otherwise may change in a block of colors
    def chaserChangeColor (self, seq_position, reverse, colors):
        current_color = math.floor(seq_position / self.strip.numPixels())
        for i in range (0, self.strip.numPixels()):
            if ((i%8 >= seq_position %8 and i%8 < seq_position%8 + 4) or 
                    (i%8 >= seq_position%8 -7 and i%8 <= seq_position%8 -5)):
                if (i < seq_position - (self.strip.numPixels() * current_color)):
                    pixel_color = current_color + 1
                    if (pixel_color >= len(colors)) :
                        pixel_color = 0
                else:
                    pixel_color = current_color
                
                self.strip.setPixelColor(i, colors[pixel_color])
            else:
                self.strip.setPixelColor(i, Color(0,0,0))
        self.strip.show()
        if (reverse == True):
            return self._seq_dec (seq_position, len(colors)*self.strip.numPixels()-1)
        else:
            return self._seq_inc (seq_position, len(colors)*self.strip.numPixels()-1)
        
        
    # chaser with black background
    # If multiple colours then a single block of colours goes across the strip
    # If single color selected then show 4 LEDs on, followed by 4 LEDs off
    def chaserBackground(self, seq_position, reverse, colors):
        # if single color selected then create a separate array with 4 x colors
        if (len(colors) < 2):
            chase_colors = [colors[0], colors[0], colors[0], colors[0]]
        else :
            chase_colors = colors
        for i in range (0, self.strip.numPixels()):
            if (i >= seq_position and i < seq_position + len(chase_colors)):
                pixel_color = chase_colors[i - seq_position]
            elif (i < seq_position - self.strip.numPixels() + len(chase_colors)):
                pixel_color = chase_colors[self.strip.numPixels() - seq_position + i]
            else:
                pixel_color = Color(0,0,0)
            self.strip.setPixelColor(i, pixel_color)
        self.strip.show()
        
        if (reverse == True):
            return self._seq_dec (seq_position, self.strip.numPixels()-1)
        else:
            return self._seq_inc (seq_position, self.strip.numPixels()-1)
            
            
    def chaserFillEnd(self, seq_position, reverse, colors):
        working_seq = seq_position  # use to calculate how far in sequence
        static_leds = 0             #  how many leds from end are static color
        num_pixels = self.strip.numPixels() # saves lots of method calls
        end_pixel = num_pixels      # current end of pixels (when calc pixel)
        
        current_color = 0
        moving_color = 0 # set to 0, but change later
        
        # loop across all static pixels
        while (working_seq > end_pixel and end_pixel > 0) :
            working_seq -= end_pixel
            end_pixel -= 1
            static_leds += 1
            
        
        # now have number of leds to light at end (static) 
        # and which led to light as moving up 
        # light up the static leds, turn all other LEDs off
        for i in range (0, num_pixels):
            if (i >= num_pixels - static_leds):
                # if revse then go from far end instead of nearest
                if (reverse == True):
                    self.strip.setPixelColor (num_pixels -i -1, colors[current_color])
                else :
                    self.strip.setPixelColor(i, colors[current_color])
            else:
                if (reverse == True):
                    self.strip.setPixelColor(num_pixels -i -1, Color(0,0,0))
                else:
                    self.strip.setPixelColor(i, Color(0,0,0))
            # If last non-static (if so use for color of moving)
            if (i == num_pixels - static_leds -1):
                moving_color = current_color
            # increment color
            current_color = self._color_inc (current_color, len(colors), reverse)
            # Set moving pixel to the determined color
            if (working_seq > 0):
                if (reverse == True):
                    self.strip.setPixelColor(num_pixels - working_seq, colors[moving_color])
                else:
                    self.strip.setPixelColor(working_seq -1, colors[moving_color])
        self.strip.show()
        if (static_leds >= num_pixels) :
            return 0
        else :
            return seq_position + 1
            
    # from first pixel to last add LeD at a time then stay lit
            
    # choose a sequence at random
    # change when each reaches 0
    def randomSeq(self, seq_position, reverse, colors):
        if (seq_position == 0):
            # if choose random then try again until get a different sequence
            while 1:
                seq_num = random.randint(0,len(self.seq_list.pixel_sequences)-1)
                self.randseq = self.seq_list.pixel_sequences[seq_num]['seq_name']
                if (self.randseq != "random"):
                    break
            # if default color when select new colors
            if (len(colors) == 1 and colors[0] == Color(255,255,255)):
                self.randcolors.clear()
                # add 4 random colors
                for i in range (0, 4):
                    randcol_pos = random.randint(0, len(self.seq_list.def_colors)-1)
                    self.randcolors.append(self.seq_list.def_colors[randcol_pos])
            else:
                self.randcolors = colors.copy()
        return self.seq_methods[self.randseq](seq_position, reverse, self.randcolors)
        

    # Helper functions 
    ######################################################
    # Increment or decrement seq_position 
    # Used by chaser methods
    def _seq_inc (self, seq_position, max_pos):
        seq_position += 1
        if (seq_position > max_pos):
            seq_position = 0
        return seq_position
                    
    # Used by other methods
    def _seq_dec (self, seq_position, max_pos):
        seq_position -= 1
        if (seq_position < 0):
            seq_position = max_pos
        return seq_position     
    
    # Increment or decrement color based on reverse = true / false
    def _color_inc (self, current_color, num_colors, reverse):
        if reverse == False:
            current_color += 1
            if (current_color >= num_colors):
                current_color = 0
        else:
            current_color -= 1
            if (current_color < 0):
                current_color = num_colors -1
        return current_color
        
        
