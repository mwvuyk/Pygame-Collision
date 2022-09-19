import pygame
import pygame.locals
from math import cos, sin, radians, sqrt
import numpy as np

def QuitGame():
    pygame.quit()
    exit()

def ParseTilemap(tilemap):
    tilearray = np.frombuffer(bytes(tilemap.replace("\n", ""),"utf-8"),"uint8")
    tilearray = np.reshape(tilearray, (-1, 16))
    tilearray = tilearray - 48
    print(tilearray)
    return tilearray

def DrawTilemap(tilearray):
    dy, dx = 0, 0
    w = 15
    for y in tilearray:
        for x in y:
            if x == 0: #Nothing here
                pass
            if x == 1: #wall
                pygame.draw.polygon(screen,(0,255,0),[(dx,dy),(dx+w,dy),(dx+w,dy+w),(dx,dy+w)])
            if x == 2: #\|
                pygame.draw.polygon(screen,(0,255,0),[(dx,dy),(dx+w,dy),(dx+w,dy+w)])
            if x == 3: #/|
                pygame.draw.polygon(screen,(0,255,0),[(dx,dy+w),(dx+w,dy+w),(dx+w,dy)])
            if x == 4: #|\
                pygame.draw.polygon(screen,(0,255,0),[(dx,dy),(dx+w,dy+w),(dx,dy+w)])
            if x == 5 or x == 6 : #|/
                pygame.draw.polygon(screen,(0,255,0),[(dx,dy),(dx+w,dy),(dx,dy+w)])
            dx += tw
        dy += tw
        dx = 0

def Angles(theta, r):
    return cos(radians(theta))*r, sin(radians(theta))*r

def ceildiv(a, b):
    return int(-(a // -b))

def lerp(a,b,t):
    return a+(b-a)*t

tilemap = """
1111111111111111
1000000000000001
1000000000001101
1000010000001101
1000000000000001
1000000000043001
1000031400051001
1000311140000001
1000111110000001
1000211150000001
1000021500000001
1000000000000001
1000000000010001
1000034000000001
1000000000000001
1111111111111111
"""




class Player:
    def __init__(self):
        self.x = 32
        self.y = 32
        self.ang = 90
        self.dir = 0
        self.size = 12
        self.tank = False
        self.lastt = np.array([])

    def GetCenter(self):
        return (self.x+0.5*self.size,self.y+0.5*self.size)

    def Controls(self):
        self.tank = not self.tank

    def TankControls(self, keys):
        self.ang += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * rotvel
        self.dir = (keys[pygame.K_UP] - keys[pygame.K_DOWN]) * vel
        return Angles(self.ang, self.dir)

    def NormControls(self,keys):
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * vel
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * vel
        return dx, dy
    
    def Draw(self):
        pygame.draw.rect(screen,(255,0,0),(self.x, self.y, self.size, self.size))
        if self.tank:
            o = Angles(self.ang, self.size/2)
            c = (self.x+0.5*self.size, self.y+0.5*self.size)
            o = tuple(np.add(o,c))
            pygame.draw.rect(screen,(0,0,255),(o[0]-self.size/8, o[1]-self.size/8, self.size/4, self.size/4))
        pygame.draw.circle(screen,(255,255,0),self.GetCenter(),self.size/2,1)
    def GetRect(self,x,y):
        return int(x//tw),int(y//tw)
    
    def CollideWithLines(self,lines,center,r):
        def LineProject(a,b,p):   #See https://en.wikipedia.org/wiki/Vector_projection. Returns projected point on line.
            def Dot2(x,y):
                return x[0]*y[0] + x[1]*y[1] #Dot product of vectors

            ap = (p[0]-a[0],p[1]-a[1]) #Vector to project
            ab = (b[0]-a[0],b[1]-a[1]) #Vector to project onto

            dist = Dot2(ap,ab)/Dot2(ab,ab) #Project vector onto line...
            return (a[0]+(dist*ab[0]),a[1]+(dist*ab[1])) #from projection onto line to absolute position in world

        def IsOnLine(p1,p2,pt): #simple check if point is on line
            return p1[0] < pt[0] < p2[0] or p1[0] > pt[0] > p2[0] or p1[1] < pt[1] < p2[1] or p1[1] > pt[1] > p2[1]

        def FindVector(pt, center, r):
            l1 = center[0] - pt[0]
            l2 = center[1] - pt[1]
            dist = sqrt(l1**2+l2**2) #distance between circle center and point
            if dist < r and dist != 0: #if the distance is less than the radius (e.g. we are colliding)
                mdist = r - dist #get the amount by which we are colliding
                return ((l1/dist)*mdist,(l2/dist)*mdist) #and spread it over the x and y vectors
            else:
                return (0,0)

        nv = [0,0]
        c = [center[0],center[1]]
        for segment in lines:
            point = LineProject(segment[0],segment[1],c)
            isonsegment = IsOnLine(segment[0],segment[1],point)
            lvector = FindVector(point, c, r)
            if isonsegment: #if the point is on the line, get pushed away by it
                nv = [sum(x) for x in zip(nv, lvector)]
                c = [sum(x) for x in zip(c, lvector)]
            else: #otherwise interact with the two end points of the line
                nv1 = FindVector(segment[0], c, r)
                nv = [sum(x) for x in zip(nv, nv1)]
                c = [sum(x) for x in zip(c, nv1)]

                nv2 = FindVector(segment[1], c, r)
                nv = [sum(x) for x in zip(nv, nv2)]
                c = [sum(x) for x in zip(c, nv2)]
        return nv

    

    def CollideStep(self):

        center = self.GetCenter()
        r = self.size/2
        gridx, gridy = self.GetRect(center[0],center[1])
        t = tiles[gridy-1:gridy+2,gridx-1:gridx+2] #Get 3x3 area around player.
        
        if not np.array_equal(self.lastt,t):
            self.lastt = t
            print(t)

        lines = [] #Turn tiles into lines.
        for t1, row in enumerate(t, -1):
            for t2, tile in enumerate(row, -1):
                tx = gridx*tw+t2*tw
                ty = gridy*tw+t1*tw
                if tile == 1:
                    lines.extend([((tx,ty),(tx+tw,ty)),((tx+tw,ty),(tx+tw,ty+tw)),((tx+tw,ty+tw),(tx,ty+tw)),((tx,ty+tw),(tx,ty))])
                elif tile == 2:
                    lines.extend([((tx,ty),(tx+tw,ty)),((tx+tw,ty),(tx+tw,ty+tw)),((tx+tw,ty+tw),(tx,ty))])
                elif tile == 3:
                    lines.extend([((tx,ty+tw),(tx+tw,ty)),((tx+tw,ty),(tx+tw,ty+tw)),((tx+tw,ty+tw),(tx,ty+tw))])
                elif tile == 4:
                    lines.extend([((tx,ty),(tx+tw,ty+tw)),((tx+tw,ty+tw),(tx,ty+tw)),((tx,ty+tw),(tx,ty))])
                elif tile == 5:
                    lines.extend([((tx,ty),(tx+tw,ty)),((tx+tw,ty),(tx,ty+tw)),((tx,ty+tw),(tx,ty))])
        for line in lines:
            pygame.draw.line(screen,(0,0,255),line[0],line[1])
        return self.CollideWithLines( lines, center, r)

    def Update(self):
        keys = pygame.key.get_pressed()       

        mx, my = self.TankControls(keys) if self.tank else self.NormControls(keys)

        for x in range(5):
            self.x += mx/5
            self.y += my/5
            dx, dy = self.CollideStep()
            self.x += dx
            self.y += dy

        self.Draw()
        
if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((256, 256))
    clock = pygame.time.Clock()
    vel = 1
    rotvel = 5
    tw = 16
    tiles = ParseTilemap(tilemap)
    screen.fill((255, 255, 255))
    pygame.display.flip()

    player = Player()

    
    while 1:
        clock.tick(60)
        screen.fill(0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                QuitGame()
            if event.type == pygame.KEYDOWN:
                print(pygame.key.name(event.key))
                if event.key == pygame.K_z:
                    player.Controls()

        DrawTilemap(tiles)
        player.Update()
        
        
        pygame.display.flip()
