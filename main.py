import Tkinter as tk

class Game(tk.Frame):
    """Game instance, a Tkinter.Frame subclass given to Tkinter.Tk() root."""
    def __init__(self, master):
        """Initialize parent Tkinter.Frame() and game environment."""
        # Init parent - Tkinter.Frame(Frame instance, Tk instance)
        tk.Frame.__init__(self, master)
        self.lives = 3
        self.width = 610
        self.height = 400
        # Tkinter.Canvas() will take up the Frame area, we can draw on it
        self.canvas = tk.Canvas(self, bg='#aaaaff', width=self.width,
                                height=self.height)

        # require .pack() by Tk to do actual placement
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self._paddle_y_start = 326
        self.paddle = Paddle(self.canvas, self.width / 2, self._paddle_y_start)

        # e.g. self.items = {'32345': Paddle, }
        # the .item property is an int that is returned as a unique reference
        # to element created by a canvas method (e.g. canvas.create_oval() or
        # canvas.create_rectangle())
        # This dict will only hold canvas items that can collide with the ball
        self.items[self.paddle.item] = self.paddle

        # Create the brick layout
        for x in range(5, self.width - 5, 75):  # 75 px step
            self.add_brick(x + 37.5, 50, 2)
            self.add_brick(x + 37.5, 70, 1)
            self.add_brick(x + 37.5, 90, 1)

        self.hud = None

        # set up game entities
        self.setup_game()

        # bind key events to movement methods
        self.canvas.focus_set()  # set focus to canvas to make sure we hear

        # We  use anonymouse function calls here as event handlers.
        # '_' is just placeholder to mean ignore the first parameter given
        # to us (a Tkinter event by bind()).
        # We do it this way because the bind() call requires a callback
        # argument, so we can't just put in self.paddle.move(10) because
        # it is not callable (it would evaluate .move(10) in place first
        # before calling the .bind() command! 
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(10))

    def setup_game(self):
        """Do all the necessary things to start the game."""
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, "Press Spacebar to start")
        # Bind only here otherwise would call start_game() each time pressed
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        """Create a Ball and store a reference in self.Paddle as well."""
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        # set the ball on top of player's paddle at start
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 310)
        self.paddle.set_ball(self.ball)  # store reference to it

    def add_brick(self, x, y, hits):
        """
        Create a Brick object.

        :param x: x-axis int location to create Brick.
        :param y: y-axis int location to create Brick.
        :param hits: int number of hits before Brick breaks.
        """
        brick = Brick(self.canvas, x, y, hits)
        # brick.item will be int that uniquely ID's that brick on canvas
        self.items[brick.item] = brick 

    def draw_text(self, x, y, text, size='40'):
        """
        Draw text message on the canvas instance.

        :param x: int x-axix location to start text
        :param y: int y-axis location to start text
        :param text: text to draw at location
        :param size: default 40. Int size of font to use
        :rtype: int that references item uniquely on canvas
        """
        font = ('Helvetica', size)
        return self.canvas.create_text(x, y, text=text, font=font)

    def update_lives_text(self):
        """Displays number of lives left on canvas."""
        text = "Lives: {}".format(self.lives)
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        """Start main loop of game."""
        # unbind pressing space to call start_game()
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        """Main game loop."""
        self.check_collisions()
        # get how many Bricks left
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0:
            self.ball.speed = None
            self.draw_text(300, 200, "You've won!")
        elif self.ball.get_position()[3] >= self.height:
            # bottom of screen, lose a life
            self.ball.speed = None
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(300, 200, "Game Over")
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()  # update position
            # use Tkinter .after() method to call game loop again
            # after(delay in ms, callback)
            self.after(50, self.game_loop)

    def check_collisions(self):
        """
        Process the ball's collisions.

        Since Ball.collide receives a list of game objects and 
        canvas.find_overlapping() returns a list of colliding items 
        with a given position, we use the dict of items to transform
        each canvas item into its corresponding game object.

        Game.items property will only contain canvas items that can 
        collide with the ball. Therefore, we only need to pass the 
        items from the Game.items dict.

        We filter the canvas items that cannot collide with the ball, 
        like text objects, and then we retrieve each game objects by
        its key.
        """
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords) # list
        # list comprehension to filter down to only objects that
        # can collide with the ball
        collideables = [self.items[x] for x in items if x in self.items]
        self.ball.collide(collideables)
        
    
class GameObject(object):
    """Base class for game entities on a Tkinter.Canvas()."""
    def __init__(self, canvas, item):
        """
        Stores the canvas and item parameters as properties of this instance
        for reference.

        :param canvas: a Tkinter.Canvas instance
        :param item: an entity/shape, e.g. a Canvas.create_oval reference
        """
        self.canvas = canvas
        self.item = item

    def get_position(self):
        """
        Returns bounding coordinates of instance's item property.

        :rtype: list of integers
        """
        return self.canvas.coords(self.item)

    def move(self, x, y):
        """
        Move the instance's item property by x horizontally, and y vertically.

        :param x: distance to move self.item horizontally in pixels
        :param y: distance to move self.item vertically in pixels
        """
        self.canvas.move(self.item, x, y)

    def delete(self):
        """Remove instance's self.item."""
        self.canvas.delete(self.item)
        

class Ball(GameObject):
    """
    Ball that bounces off solid objects on screen. Stores information
    about speed, direction, and radius of the ball.
    """
    def __init__(self, canvas, x, y):
        """Creates ball shape using canvas.create_oval()."""
        self.radius = 10
        self.direction = [1, -1]  # right and up
        self.speed = 10
        
        # self.item value will be an integer, which is ref num returned by method
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='white')
        # now call parent constructor with our required item
        GameObject.__init__(self, canvas, item)

    def update(self):
        """Logic for changing Ball direction based on collisions."""

        # ---------------------------------------------------------
        # BOUNDS COLLISIONS
        # ---------------------------------------------------------
        ball_coords = self.get_position()
        width = self.canvas.winfo_width()  # TODO: move to call once
        
        if ball_coords[0] <= 0 or ball_coords[2] >= width:
            self.direction[0] *= -1  # reverse x vector
        if ball_coords[1] <=0:
            self.direction[1] *= -1  # reverse y vector
        x = self.direction[0] * self.speed  # scale by Ball's speed
        y = self.direction[1] * self.speed
        self.move(x, y)  # inherited method


    def collide(self, game_objects):
        """
        Handles the outcome of collision with one or more objects.

        :param game_objects: list of colliding objects.

        Code Explanation:
        # First get center x of Ball
        # x0, y0 is top left corner, x1, y1 is bottomright corner
        ball_coords = self.get_position() # -> [x0, y0, x1, y1]
        # we add the start and end x positions and * 0.5 to get midx
        ball_center_x = (ball_coords[0] + coords[2]) * 0.5  # center
        brick_coords = brick.get_position() # -> [x0, y0, x1, y1]
        # if ball_center is greater than lower right of brick, meaning
        # ball center is to right of right side of brick during collision
        if ball_center_x > brick_coords[2]:
            self.direction[0] = 1  # ball x to right
        # check is ball center is left of the left side of brick 
        # during collision
        elif ball_center_x < brick_coords[0]:
            self.direction[0] = -1  # ball x to the left
        # else case means ball_center is between left and right x of brick
        # which means a top/bottom hit, so we just reverse y-vector of ball
        else:
            self.direction[1] *= -1

        Above is valid for when ball hits the paddle or a single brick. But
        if we hit two bricks at the same time things get hairy. We simplify
        by assuming multiple brick collisions can only happen from above or
        below. That means that we change the y-axis direction of the ball 
        without calculating the position of the colliding bricks. 

        So what we do is guard all of the above by checking how many 
        colliding objects we have, in the argument game_objects, and if it
        is two or more we can just flip the y-axis on the ball and be done.
        If not, we have to do more investigation and do all of the above.      
        """
        ball_coords = self.get_position()
        ball_center_x = (ball_coords[0] + ball_coords[2]) * 0.5  # same as / 2

        if len(game_objects) > 1:  # 2+ collisions, just flip y-axis and done
            self.direction[1] *= -1
        elif len(game_objects) == 1:  # investigate more if just one collision
            game_object = game_objects[0]
            coords = game_object.get_position()
            if ball_center_x > coords[2]:
                self.direction[0] = 1
            elif ball_center_x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1
        # Do below regardless of how many collisions came in
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()  # decrement hit counter, etc. in Brick class

    
class Paddle(GameObject):
    """
    The player's paddle. A set_ball method stores a reference to the ball, 
    which can be moved with the ball before the game starts.
    """
    def __init__(self, canvas, x, y):
        """
        Create a Paddle instance using canvas.create_rectangle().

        :param canvas: a Tkinter.Canvas() instance
        :param x: the horizontal axis location (int)
        :param y: the vertical axis location (int)
        """
        self.width = 80
        self.height = 10
        self.ball = None

        # item will be int ref num returned by create_rectangle()
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='blue')
        # call parent class now with our require item argument
        GameObject.__init__(self, canvas, item)

    def set_ball(self, ball):
        """Store a reference to a ball on this instance."""
        self.ball = ball

    def move(self, offset):
        """
        Move the Paddle on the Tkinter.Canvas within bounds.
        
        Contained here is the pre-move logic. The actual move is 
        done by calling our parent GameObject.move() method.

        :param offset: integer. amount to move in pixels left or right.
        """
        coords = self.get_position()  # e.g., [int, int, int, int]
        width = self.canvas.winfo_width()
        # bounds check
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            GameObject.move(self, offset, 0)  # 0 is y-axis
            # Below happens when the game has not been started; move the ball
            if self.ball is not None:
                self.ball.move(offset, 0)  # Call Ball inherited move() method
            

class Brick(GameObject):
    """Ball objects destroy these canvas rectangle built objects when hit."""
    COLORS = {1: '#999999', 2: '#555555', 3: '#222222'}

    def __init__(self, canvas, x, y, hits):
        """
        Initialize a Brick object.
        
        :param canvas: a Tkinter.Canvas() instance
        :param x: Where to place it on horizontal x axis
        :param y: Where to place it on the vertical x axis
        :param hits: number of hits Brick can take before 'breaking'
        """
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]  # hits arg must be int 1,2, or 3

        # tags keyword is so we can reference it easy on canvas
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        # now call parent class with our require item
        GameObject.__init__(self, canvas, item)

    def hit(self):
        """Decrement hits counter. Delete instance if at 0."""
        self.hits -= 1
        if self.hits == 0:
            self.delete()  # inherited from GameObject()
        else:  # repaint next color to indicate Brick was hit
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])
            
        
        
if __name__ == "__main__":
    # Create the root app and then create the Game instance (a tk.Frame()) 
    root = tk.Tk()
    root.title('Tkinter Breakout')
    # Frame() needs a Tk() instance as its parent, we pass our root app
    game = Game(root)
    game.mainloop()
