from typing import List, Tuple, Optional
from medford_linereader import LineReturn
import re

class Detail :
    major_token: str
    minor_token: Optional[str]

    _fulldesc: List[LineReturn] # keep LineReturns so we can extract comments, linenos later

    
    def __init__(self, lines : List[LineReturn]) :
        '''
        Create a Detail object from one DETAIL type LineReturn and any number of CONT type LineReturns.

        Parameters
        ------
        lines: List[LineReturn]
        '''
        if len(lines) == 0 :
            raise ValueError("At least one LineReturn must be provided to create a Detail object.")
        
        detail_line : LineReturn = lines[0]
        if not detail_line.is_detail :
            raise ValueError("First provided LineReturn must be of type DETAIL.")
        
        self._fulldesc : List[LineReturn] = lines

        # find major, minor tokens from first line
        major_minor_reg : str = "@(?<major>[A-Za-z_]+)(-(?<minor>[A-Za-z]))? "

        mm_res : Optional[re.Match[str]] = re.match(major_minor_reg, detail_line.line)
        if mm_res == None :
            # try to figure out what went wrong?
            # possibilities :
            # - poorly formatted major (@Major3-Minor Content)
            # - poorly formatted minor (@Major-Minor3 Content)
            # - missing both (@ Content)
            # - no trailing space (@Major-MinorContent\n)
            # - leading space?? ( @Major-Minor Content) <- no, impossible given how linereader finds lines
            # for now, cry and give up.
            # TODO : change to Medford error
            raise NotImplementedError("Something went horribly wrong when trying to find the major and minor tokens.")
        else :
            mm_match_res : re.Match[str] = mm_res
            match_grps = mm_match_res.groupdict()
            
            self.major_token = match_grps['major']
            if 'minor' in match_grps.keys() :
                self.minor_token = match_grps['minor']
            else :
                self.minor_token = None

        return

    def validate(self) :
        return