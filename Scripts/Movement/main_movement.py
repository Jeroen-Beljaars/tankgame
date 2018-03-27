import bge

def keyDown(key_code, status=bge.logic.KX_INPUT_ACTIVE):
    """ 
    This method checks if the key (key_code) is active 
    i.e. keyboard(bge.events.WKEY) checks if the w_key is being pressed
    """
    if bge.logic.keyboard.events[key_code] == status:
        return True
    return False

class Player(bge.types.KX_GameObject):
    """ The player object """
    def __init__(self, own):
        # Initialize the movement speed
        # Forward & backwards speed
        self.speed = 0.1

        # Rotation speed
        self.rot_speed = 0.05
        
        # Which user object 
        self.user = self["user"]
        print(self.user)
    
    def movement(self):
        """ Handles the players movement """
        keyboard = self.user.keyboard.keyDown
        
        # Basic movement (forward, backwards, left, right)
        w_key = keyboard(bge.events.WKEY)
        s_key = keyboard(bge.events.SKEY)
        a_key = keyboard(bge.events.AKEY)
        d_key = keyboard(bge.events.DKEY)

        # Back and forward movement
        if w_key:
            self.applyMovement((self.speed,0,0), True)
        elif s_key:
            self.applyMovement((-self.speed,0,0), True)
        
        # Rotation
        if a_key:
            self.applyRotation((0,0,self.rot_speed), False)
        elif d_key:
            self.applyRotation((0,0,-self.rot_speed), False)


def main(cont):
    # Get the tank obj
    own = cont.owner
    
    # Check if the player has been initialized
    if not "init" in own:
        # the player is not initialized yet
        # Create an player obj
        own["init"] = 1
        Player(own)
    else:
        # The player has been initialized.
        # Run the movement handler
        own.movement()
