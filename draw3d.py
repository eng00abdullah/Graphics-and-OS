"""
draw3d.py  —  Enhanced 3D Primitives for OS Scheduler
"""
from OpenGL.GL  import *
from OpenGL.GLU import *
import math

_quad = None

def get_quad():
    global _quad
    if _quad is None:
        _quad = gluNewQuadric()
        gluQuadricNormals(_quad, GLU_SMOOTH)
    return _quad

def setup_lighting():
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_NORMALIZE)
    glLightfv(GL_LIGHT0, GL_POSITION, [1.2, 2.0, 2.5, 0.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.20, 0.20, 0.30, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.7, 0.7, 0.9, 1.0])
    glLightfv(GL_LIGHT1, GL_POSITION, [-1.5, 0.5, -1.0, 0.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE,  [0.25, 0.25, 0.45, 1.0])
    glLightfv(GL_LIGHT1, GL_AMBIENT,  [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR,  [0.6, 0.6, 0.8, 1.0])
    glMateriali (GL_FRONT, GL_SHININESS, 52)

def lighting_off():
    glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)

def draw_bar_3d(x, y, z, w, h, d, color, alpha=1.0):
    r,g,b = color
    glPushMatrix()
    glTranslatef(x+w/2, y+h/2, z+d/2)
    glBegin(GL_QUADS)
    # Front  (full brightness)
    glNormal3f(0,0,1);  glColor4f(r,g,b,alpha)
    glVertex3f(-w/2,-h/2, d/2); glVertex3f(w/2,-h/2,d/2)
    glVertex3f( w/2, h/2, d/2); glVertex3f(-w/2, h/2,d/2)
    # Back
    glNormal3f(0,0,-1); glColor4f(r*0.7,g*0.7,b*0.7,alpha)
    glVertex3f( w/2,-h/2,-d/2); glVertex3f(-w/2,-h/2,-d/2)
    glVertex3f(-w/2, h/2,-d/2); glVertex3f( w/2, h/2,-d/2)
    # Top  (brightest — catches the light)
    glNormal3f(0,1,0);  glColor4f(min(r*1.35,1),min(g*1.35,1),min(b*1.35,1),alpha)
    glVertex3f(-w/2,h/2, d/2); glVertex3f(w/2,h/2,d/2)
    glVertex3f( w/2,h/2,-d/2); glVertex3f(-w/2,h/2,-d/2)
    # Bottom
    glNormal3f(0,-1,0); glColor4f(r*0.45,g*0.45,b*0.45,alpha)
    glVertex3f(-w/2,-h/2,-d/2); glVertex3f(w/2,-h/2,-d/2)
    glVertex3f( w/2,-h/2, d/2); glVertex3f(-w/2,-h/2, d/2)
    # Right
    glNormal3f(1,0,0);  glColor4f(r*0.82,g*0.82,b*0.82,alpha)
    glVertex3f(w/2,-h/2,d/2); glVertex3f(w/2,-h/2,-d/2)
    glVertex3f(w/2, h/2,-d/2); glVertex3f(w/2, h/2,d/2)
    # Left  (darkest side)
    glNormal3f(-1,0,0); glColor4f(r*0.60,g*0.60,b*0.60,alpha)
    glVertex3f(-w/2,-h/2,-d/2); glVertex3f(-w/2,-h/2,d/2)
    glVertex3f(-w/2, h/2, d/2); glVertex3f(-w/2, h/2,-d/2)
    glEnd()
    glPopMatrix()

def draw_sphere_3d(cx,cy,cz,radius,color,alpha=1.0):
    r,g,b=color; glColor4f(r,g,b,alpha)
    glPushMatrix(); glTranslatef(cx,cy,cz)
    gluSphere(get_quad(),radius,28,18)
    glPopMatrix()

def draw_cylinder_3d(cx,cy,cz,radius,height,color,alpha=1.0):
    r,g,b=color; glColor4f(r,g,b,alpha)
    glPushMatrix(); glTranslatef(cx,cy,cz)
    glRotatef(-90,1,0,0)
    q=get_quad()
    gluCylinder(q,radius,radius,height,22,3)
    glTranslatef(0,0,height); gluDisk(q,0,radius,22,1)
    glTranslatef(0,0,-height); glRotatef(180,1,0,0); gluDisk(q,0,radius,22,1)
    glPopMatrix()

def draw_cone_3d(cx,cy,cz,radius,height,color,alpha=1.0):
    r,g,b=color; glColor4f(r,g,b,alpha)
    glPushMatrix(); glTranslatef(cx,cy,cz); glRotatef(-90,1,0,0)
    q=get_quad()
    gluCylinder(q,radius,0,height,16,1); glRotatef(180,1,0,0); gluDisk(q,0,radius,16,1)
    glPopMatrix()

def draw_grid_floor(x0,z0,x1,z1,y,step=40,color=(0.10,0.12,0.35),alpha=0.4):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(*color,alpha); glLineWidth(0.7)
    glBegin(GL_LINES)
    xi=x0
    while xi<=x1+0.1:
        glVertex3f(xi,y,z0); glVertex3f(xi,y,z1); xi+=step
    zi=z0
    while zi<=z1+0.1:
        glVertex3f(x0,y,zi); glVertex3f(x1,y,zi); zi+=step
    glEnd()
    glEnable(GL_LIGHTING)
