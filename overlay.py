import sys, os, math, ctypes, collections, statistics
from PyQt5 import QtCore, QtGui, QtWidgets
import cv2, numpy as np, mss
from pynput import keyboard

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("OverlayTool.CompanyName.1.0")

RADIUS = 80
PATCH = RADIUS * 2
C1, C2 = 50, 150
HOUGH, MINLEN, AVG_WIN = 80, 50, 6
DOT_R, DOT_DIST = 4, 6
HELP_LINES = ("Ctrl – фиксировать", "Shift – удалить всё")
PANEL_SIZE, CLOSE_SZ = 160, 16
BORDER_COL = QtGui.QColor(0, 0, 139)

def rp(r): return os.path.join(getattr(sys, "_MEIPASS", os.path.abspath(".")), r)
ICON_PATH = rp("app.ico")

def sample_mid(edges, seg, n=25):
    x1, y1, x2, y2 = seg
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    if ln == 0: return [], 1
    nx, ny = -dy / ln, dx / ln
    h, w = edges.shape
    mids, ws = [], []
    for i in range(n):
        t = (i + .5) / n
        cx, cy = x1 + t * dx, y1 + t * dy
        if not (0 <= cx < w and 0 <= cy < h): continue
        pos = neg = 0
        while 0 <= cx + (pos+1)*nx < w and 0 <= cy + (pos+1)*ny < h and edges[int(cy + (pos+1)*ny), int(cx + (pos+1)*nx)]: pos += 1
        while 0 <= cx - (neg+1)*nx < w and 0 <= cy - (neg+1)*ny < h and edges[int(cy - (neg+1)*ny), int(cx - (neg+1)*nx)]: neg += 1
        if pos + neg + 1:
            offs = (pos - neg) / 2
            mids.append((cx + nx * offs, cy + ny * offs))
            ws.append(pos + neg + 1)
    return mids, (max(ws) if ws else 1)

def pca(points):
    pts = np.asarray(points, float)
    c = pts.mean(0)
    _, _, vt = np.linalg.svd(pts - c)
    v = vt[0] / np.hypot(*vt[0])
    return c, v

def ext(p, v, w, h):
    t = []
    if v[0]: t += [-p[0]/v[0], (w-p[0])/v[0]]
    if v[1]: t += [-p[1]/v[1], (h-p[1])/v[1]]
    pts = [(int(p[0]+k*v[0]), int(p[1]+k*v[1])) for k in t if 0<=p[0]+k*v[0]<=w and 0<=p[1]+k*v[1]<=h]
    return (*pts[0], *pts[1]) if len(pts)>=2 else (0,0,0,0)

def nearest(lines,cx,cy):
    best,dmin=None,1e9
    for x1,y1,x2,y2 in lines:
        px,py=x2-x1,y2-y1; n=px*px+py*py
        if not n: continue
        u=max(0,min(1,((cx-x1)*px+(cy-y1)*py)/n))
        ix,iy=x1+u*px,y1+u*py; d=math.hypot(ix-cx,iy-cy)
        if d<dmin: dmin,best=d,(x1,y1,x2,y2)
    if dmin>RADIUS: return None
    return best

class Help(QtWidgets.QWidget):
    closed = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__(None, QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowIcon(QtGui.QIcon(ICON_PATH))
        g=QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.setGeometry(g.right()-PANEL_SIZE-10, g.bottom()-PANEL_SIZE-10, PANEL_SIZE, PANEL_SIZE)
        self.hover=False; self.setMouseTracking(True)
    def paintEvent(self,_):
        p=QtGui.QPainter(self); p.setRenderHint(QtGui.QPainter.Antialiasing)
        r=self.rect()
        p.setPen(QtCore.Qt.NoPen); p.setBrush(QtGui.QColor(0,0,0)); p.drawRoundedRect(r,12,12)
        p.setPen(QtGui.QPen(BORDER_COL,4)); p.setBrush(QtCore.Qt.NoBrush); p.drawRoundedRect(r.adjusted(2,2,-2,-2),12,12)
        f=p.font(); f.setPointSize(9); p.setFont(f); fm=QtGui.QFontMetrics(f)
        y0=(self.height()-len(HELP_LINES)*fm.height())//2
        p.setPen(QtCore.Qt.white)
        for i,t in enumerate(HELP_LINES):
            p.drawText(0,y0+fm.ascent()+i*fm.height(),self.width(),fm.height(),QtCore.Qt.AlignHCenter,t)
        s=int(CLOSE_SZ*(1.3 if self.hover else 1)); self.cr=QtCore.QRect(r.right()-s-8,r.top()+8,s,s)
        p.setPen(QtGui.QPen(QtCore.Qt.white,2)); p.drawLine(self.cr.topLeft(),self.cr.bottomRight()); p.drawLine(self.cr.bottomLeft(),self.cr.topRight()); p.end()
    def _h(self,pos):
        h=self.cr.contains(pos)
        if h!=self.hover:
            self.hover=h; self.setCursor(QtCore.Qt.PointingHandCursor if h else QtCore.Qt.ArrowCursor); self.update()
    def mouseMoveEvent(self,e): self._h(e.pos())
    def leaveEvent(self,_): self._h(QtCore.QPoint(-1,-1))
    def mousePressEvent(self,e): 
        if self.cr.contains(e.pos()): self.closed.emit()

class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__(None, QtCore.Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        g=QtWidgets.QApplication.primaryScreen().geometry(); self.setGeometry(g)
        self.img=QtGui.QImage(g.width(),g.height(),QtGui.QImage.Format_ARGB32)
        self.fixed,self.cand,self.dots,self.cur=[],None,[],(0,0)
        hwnd=int(self.winId()); style=ctypes.windll.user32.GetWindowLongW(hwnd,-20)
        ctypes.windll.user32.SetWindowLongW(hwnd,-20,style|0x80000|0x20)
    def lock(self):
        if not self.cand: return
        seg,col,th=self.cand
        for s2,_,_ in self.fixed:
            x1,y1,x2,y2=seg; x3,y3,x4,y4=s2
            den=(x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
            if not den: continue
            px=((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4))/den
            py=((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4))/den
            self.dots.append((int(px),int(py)))
        self.fixed.append(self.cand); self.cand=None; self.update()
    def clear_all(self):
        self.fixed.clear(); self.dots.clear(); self.cand=None; self.update()
    def set_cand(self,c): self.cand=c; self.update()
    def set_cursor(self,p): self.cur=p
    def paintEvent(self,_):
        self.img.fill(QtCore.Qt.transparent); p=QtGui.QPainter(self.img)
        for seg,col,th in self.fixed+([self.cand] if self.cand else []):
            pen=QtGui.QPen(QtGui.QColor(int(col[2]),int(col[1]),int(col[0]),230),th); pen.setCosmetic(False)
            p.setPen(pen); p.drawLine(*seg)
        for x,y in self.dots:
            a=80 if math.hypot(x-self.cur[0],y-self.cur[1])<DOT_DIST else 255
            p.setPen(QtCore.Qt.NoPen); p.setBrush(QtGui.QColor(255,0,0,a))
            p.drawEllipse(QtCore.QPointF(x,y),DOT_R,DOT_R)
        p.end(); qp=QtGui.QPainter(self); qp.drawImage(0,0,self.img); qp.end()

class Controller:
    def __init__(self):
        self.app=QtWidgets.QApplication(sys.argv); self.app.setWindowIcon(QtGui.QIcon(ICON_PATH))
        self.ov=Overlay(); self.ov.show()
        self.hp=Help(); self.hp.closed.connect(self.app.quit); self.hp.show(); self.hp.raise_()
        self.sct=mss.mss(); self.hist=collections.deque(maxlen=AVG_WIN)
        keyboard.Listener(on_press=self.on_key).start()
        self.t=QtCore.QTimer(); self.t.timeout.connect(self.tick); self.t.start(120)
    def on_key(self,k):
        if k in (keyboard.Key.ctrl_l,keyboard.Key.ctrl_r): self.ov.lock()
        elif k in (keyboard.Key.shift,keyboard.Key.shift_l,keyboard.Key.shift_r): self.ov.clear_all()
    def snap(self): return np.array(self.sct.grab(self.sct.monitors[0]))[:,:,:3]
    def tick(self):
        img=self.snap(); h,w=img.shape[:2]
        cx,cy=QtGui.QCursor.pos().x(),QtGui.QCursor.pos().y(); self.ov.set_cursor((cx,cy))
        x0,y0=max(0,cx-RADIUS),max(0,cy-RADIUS); x1,y1=min(w,cx+RADIUS),min(h,cy+RADIUS)
        gray=cv2.cvtColor(img[y0:y1,x0:x1],cv2.COLOR_BGR2GRAY); edges=cv2.Canny(gray,C1,C2)
        lns=cv2.HoughLinesP(edges,1,math.pi/180,HOUGH,minLineLength=MINLEN,maxLineGap=10)
        if lns is None: self.hist.clear(); self.ov.set_cand(None); return
        raw=nearest([tuple(l[0]) for l in lns],cx-x0,cy-y0)
        if raw is None: self.hist.clear(); self.ov.set_cand(None); return
        mids,width=sample_mid(edges,raw)
        if len(mids)<2: self.hist.clear(); self.ov.set_cand(None); return
        c,v=pca(mids); seg=ext((c[0]+x0,c[1]+y0),v,w,h)
        self.hist.append(seg); avg=tuple(int(statistics.mean(p[i] for p in self.hist)) for i in range(4))
        mask=np.zeros((h,w),np.uint8); cv2.line(mask,(avg[0],avg[1]),(avg[2],avg[3]),255,width)
        pts=np.column_stack(np.where(mask==255))
        col=np.mean(img[pts[:,0],pts[:,1]],axis=0) if len(pts) else (0,255,0)
        self.ov.set_cand((avg,col,width))
    def run(self): sys.exit(self.app.exec_())

if __name__=="__main__":
    Controller().run()
