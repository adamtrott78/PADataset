#!/usr/bin/env python3
"""Build the locked MILCOM deck. Requires Pillow, fontconfig and pdftocairo.

SVGs are standalone: canonical PNG bytes and converted s23 vector art are embedded.
No scientific artwork is synthesized. OTA slots are intentionally pending.
"""
from pathlib import Path
from contextlib import contextmanager
from html import escape
import base64
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'slides'
BG, INK, SECOND, BORDER, PANEL = '#F7F9FC', '#102235', '#5D6C7B', '#D8E1EA', '#EEF3F7'
BLUE, GREEN, RED, AMBER, PURPLE, GRAY = '#1F6FEB', '#2E8B57', '#C63D4F', '#E39A27', '#6C5CE7', '#8A98A8'
TINT = {BLUE:'#EAF2FF', GREEN:'#EDF7F0', RED:'#FBEFF1', AMBER:'#FFF6E8', PURPLE:'#F2EFFF'}
FONT = 'Arial, Helvetica, sans-serif'
FONTS = {b: subprocess.check_output(['fc-match','-f','%{file}', 'Arial:style=Bold' if b else 'Arial'], text=True) for b in (False, True)}
NAMES = ['title','closed_set_gap','pa_taxonomy','ota_dataset','operating_requirement','dqnguard_architecture','surrogate_calibration','main_results','target_surrogate_matrix','surrogate_diagnostics','multi_surrogate_future','takeaways']
TITLES = [
 'DQNGuard: Towards Open-World RF Preliminary-Action Detection',
 'Closed-set RF classifiers cannot say “I don\'t know”',
 'Preliminary Actions capture RF behavior, not final attack labels',
 'We evaluate the same five behaviors over-the-air across three protocol families',
 'Unknown detection is only useful if known behavior stays usable',
 'DQNGuard adds a budgeted open-world decision layer to the PA classifier',
 'A surrogate unknown shapes the DQN; the true unknown remains unseen until test',
 'DQNGuard gives the strongest usable operating point at low known rejection',
 'Surrogate usefulness depends strongly on the unseen target',
 'No simple target-blind rule reliably predicts the best surrogate',
 'VarMax can search across surrogates; DQNGuard must learn how to combine them',
 'DQNGuard improves the operating point—but surrogate transfer remains the next challenge',
]

def width(s, size, bold=False):
    return ImageFont.truetype(FONTS[bold], size).getlength(s)

def wrap(s, maxw, size, bold=False):
    result=[]
    for para in s.split('\n'):
        line=''
        for word in para.split():
            trial=(line+' '+word).strip()
            if line and width(trial,size,bold)>maxw:
                result.append(line); line=word
            else: line=trial
        result.append(line)
    return result

class Slide:
    def __init__(self, n, supporting=None):
        self.n=n; self.parts=[]; self.texts=[]
        self.add(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1920" height="1080" viewBox="0 0 1920 1080" version="1.1" id="slide{n:02}" role="img" aria-labelledby="slide_title">')
        self.add(f'<title id="slide_title">{escape(TITLES[n-1])}</title>')
        self.add('<desc>Implementation of SVG_PRODUCTION_SPEC.md. Canonical scientific assets retain their original artwork.</desc>')
        self.add('<defs>')
        for c in (INK,BLUE,GREEN,RED,AMBER,GRAY,PURPLE):
            self.add(f'<marker id="arrow{c[1:]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="3" markerHeight="3" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>')
        self.add('</defs>')
        self.rect(0,0,1920,1080,BG,stroke='none',r=0,id='background')
        if n>1:
            size=60 if width(TITLES[n-1],60,True)<=1728 else 52
            lines=wrap(TITLES[n-1],1728,size,True)
            assert len(lines)<=2
            with self.group('title_group'):
                self.text(96,116 if len(lines)==1 else 103,lines,size,True,leading=54)
            if supporting:
                with self.group('supporting_sentence'):
                    self.text(96,186 if len(lines)==1 else 193,supporting,29,color=SECOND,maxw=1728,leading=31)
    def add(self,s): self.parts.append(s)
    @contextmanager
    def group(self,id):
        self.add(f'<g id="{id}">'); yield; self.add('</g>')
    def rect(self,x,y,w,h,fill='white',stroke=BORDER,r=18,sw=2,id=None):
        self.add(f'<rect {f"id={chr(34)}{id}{chr(34)}" if id else ""} x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    def text(self,x,y,s,size=26,bold=False,color=INK,maxw=None,anchor='start',leading=None,id=None):
        lines=s if isinstance(s,list) else wrap(s,maxw,size,bold) if maxw else s.split('\n')
        leading=leading or size*1.22
        attrs=f' id="{id or "text_"+str(len(self.texts))}"'
        self.add(f'<text{attrs} x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{anchor}">')
        for i,line in enumerate(lines):
            yy=y+i*leading
            self.add(f'<tspan x="{x}" y="{yy}">{escape(line)}</tspan>')
            self.texts.append((x,yy,line,size,bold,anchor))
        self.add('</text>')
        return y+(len(lines)-1)*leading
    def line(self,x1,y1,x2,y2,color=BORDER,sw=2):
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"/>')
    def arrow(self,pts,color=INK,id=None):
        attr=f' id="{id}"' if id else ''
        self.add(f'<polyline{attr} points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{color}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow{color[1:]})"/>')
    def node(self,id,x,y,w,h,label,color=INK,size=26,bold=True,fill=None):
        with self.group(id):
            self.rect(x,y,w,h,fill or TINT.get(color,'white'),color if color!=INK else BORDER)
            lines=wrap(label,w-30,size,bold)
            self.text(x+w/2,y+h/2-(len(lines)-1)*size*.61+size*.34,lines,size,bold,color,anchor='middle')
    def image(self,id,x,y,w,h):
        with self.group(id):
            self.add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{MATRIX}"/>')
    def save(self):
        self.add('</svg>')
        value='\n'.join(self.parts)+'\n'
        root=ET.fromstring(value)
        assert root.attrib['viewBox']=='0 0 1920 1080'
        ids=[e.attrib['id'] for e in root.iter() if 'id' in e.attrib]
        assert len(ids)==len(set(ids)), 'duplicate IDs'
        assert '<foreignObject' not in value
        for x,y,line,size,bold,anchor in self.texts:
            assert size>=20
            tw=width(line,size,bold)
            left=x-tw/2 if anchor=='middle' else x-tw if anchor=='end' else x
            assert left>=90 and left+tw<=1830,(self.n,line,left,tw)
            assert 60<=y-size*.8 and y<=1035,(self.n,line,y)
        path=OUT/f'slide{self.n:02}_{NAMES[self.n-1]}.svg'
        path.write_text(value)
        print(path.name)

MATRIX=base64.b64encode((ROOT/'assets/figures/target_surrogate_unknown_f1_matrix.png').read_bytes()).decode()

def slide01():
    s=Slide(1)
    s.text(100,100,'MILCOM 2026',22,True,id='conference_tag')
    with s.group('title_group'):
        s.text(96,230,'DQNGuard',72,True,BLUE,id='title_dqnguard')
        s.text(96+width('DQNGuard',72,True),230,': Towards',72,True)
        s.text(96,305,['Open-World RF','Preliminary-Action Detection'],72,True,leading=75,id='title_remaining_lines')
        s.text(96,455,'Open-set recognition for over-the-air RF behavioral evidence',30,color=SECOND,maxw=1010,id='subtitle')
    with s.group('author_group'):
        s.text(96,825,'Adam Trott',30,True,id='presenter')
        s.text(96,870,'Cameron Popillo • Nathaniel D. Bastian • Roulin Zhou • Gokhan Kul',23,id='coauthors')
        s.text(96,910,'University of Massachusetts Dartmouth • Johns Hopkins University',22,color=SECOND,id='affiliations')
    with s.group('hero_group'):
        with s.group('rf_observation_card'):
            s.rect(1260,235,480,150)
            s.text(1500,276,'RF observation',29,True,anchor='middle')
            pts=[(1290,336),(1310,336),(1320,322),(1331,352),(1342,302),(1353,362),(1364,320),(1375,336),(1410,336),(1422,326),(1434,347),(1446,314),(1458,357),(1470,323),(1482,336),(1520,336),(1530,310),(1540,362),(1550,319),(1560,344),(1570,336),(1610,336),(1620,322),(1630,350),(1640,308),(1650,360),(1660,326),(1670,336),(1710,336)]
            s.add('<polyline id="decorative_trace" points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="none" stroke="{SECOND}" stroke-width="3"/>')
        s.arrow([(1500,385),(1500,440)],id='arrow_rf_to_classifier')
        s.node('classifier_node',1330,445,340,100,'PA classifier',fill=PANEL,size=30)
        s.arrow([(1500,545),(1500,610)],id='arrow_classifier_to_guard')
        s.node('dqnguard_node',1300,615,400,120,'DQNGuard',BLUE,36)
        with s.group('branch_connector'):
            s.line(1500,735,1500,785,INK,4)
            s.arrow([(1500,785),(1340,785),(1340,820)],GREEN)
            s.arrow([(1500,785),(1660,785),(1660,820)],RED)
        s.node('known_node',1205,825,270,105,'KNOWN PA ✓',GREEN,27)
        s.node('unknown_node',1525,825,270,105,'UNKNOWN ?',RED,27)
    s.save()

def slide02():
    s=Slide(2,'Unseen behavior is forced into a known label, even when the prediction is wrong.')
    for x,openworld in [(96,False),(984,True)]:
        with s.group('open_world_panel' if openworld else 'closed_set_panel'):
            s.rect(x,235,840,710)
            s.text(x+32,285,'OPEN-WORLD REQUIREMENT' if openworld else 'CLOSED-SET CLASSIFIER',32,True)
            s.text(x+32,345,'Allowed outputs: Scan | Burst | Hop'+(' | UNKNOWN' if openworld else ''),26)
            for y,novel in [(395,False),(635,True)]:
                with s.group(('open' if openworld else 'closed')+('_novel_case' if novel else '_known_case')):
                    s.rect(x+24,y,792,205 if not novel else 220,PANEL,stroke='none',r=12)
                    s.node(('open' if openworld else 'closed')+('_novel_input' if novel else '_known_input'),x+42,y+56,214,92,'Novel RF\nbehavior' if novel else 'Known Burst\nbehavior',RED if novel else GREEN,25,False)
                    s.arrow([(x+265,y+102),(x+300,y+102)])
                    s.node(('open' if openworld else 'closed')+('_novel_decision' if novel else '_known_decision'),x+310,y+56,205,92,'open-world\ndecision' if openworld else 'RF classifier',size=25)
                    s.arrow([(x+525,y+102),(x+561,y+102)])
                    if novel and not openworld:
                        s.text(x+689,y+58,'forced known prediction:',20,color=SECOND,anchor='middle')
                    s.node(('open' if openworld else 'closed')+('_novel_output' if novel else '_known_output'),x+573,y+75,218,58,'UNKNOWN ✓' if novel and openworld else 'Hop ✕' if novel else 'Burst ✓',RED if novel else GREEN,26)
            s.text(x+32,898,'Preserve known evidence.\nIsolate unfamiliar behavior.' if openworld else '“Unknown” is not an available output.',26,True,leading=31)
    s.save()

def slide03():
    s=Slide(3,'Preliminary Actions are observable RF behaviors, not final attack-technique labels.')
    with s.group('behavior_cards'):
        for x,name,desc in zip([96,446,796,1146,1496],['Scan','Burst','Sustain','Hop','Replay'],['Discovery-like activity','Short transmissions + quiet gaps','Persistent channel occupancy','Frequency dwell + revisits','Repeated waveform / template']):
            with s.group(name.lower()+'_card'):
                s.rect(x,255,326,545)
                s.text(x+163,307,name,32,True,anchor='middle')
                s.rect(x+18,340,290,300,PANEL,r=12,id=name.lower()+'_ota_slot')
                s.text(x+163,480,['OTA RF example','pending'],24,color=SECOND,anchor='middle')
                s.text(x+26,690,desc,26,maxw=276)
    for x,id,heading,body in [(96,'tells_us_box','WHAT IT TELLS US','Observable RF behavior'),(984,'does_not_claim_box','WHAT IT DOES NOT CLAIM','Final attack-technique attribution')]:
        with s.group(id):
            s.rect(x,835,840,115,PANEL,stroke='none')
            s.text(x+28,876,heading,24,True)
            s.text(x+28,920,body,29)
    s.text(96,995,'Same behavioral taxonomy evaluated across WiFi, Bluetooth, and Zigbee.',21,color=SECOND,id='optional_protocol_footer')
    s.save()

def slide04():
    s=Slide(4,'WiFi, Bluetooth, and Zigbee each express Scan, Burst, Sustain, Hop, and Replay behavior in captured RF.')
    with s.group('dataset_matrix'):
        s.text(663,275,'5 BEHAVIORS × 3 PROTOCOLS',30,True,anchor='middle',id='matrix_heading')
        behaviors=['Scan','Burst','Sustain','Hop','Replay']
        for j,name in enumerate(behaviors):
            x=225+j*198
            s.text(x+90,325,name,26,True,anchor='middle')
        for i,protocol in enumerate(['WiFi','Bluetooth','Zigbee']):
            y=350+i*176
            s.text(96,y+88,protocol,23,True)
            for j,name in enumerate(behaviors):
                x=225+j*198
                with s.group(f'{protocol.lower()}_{name.lower()}_ota_slot'):
                    s.rect(x,y,180,160,PANEL,r=12)
                    s.text(x+90,y+73,[protocol,name],22,color=SECOND,anchor='middle')
    with s.group('ota_capture_panel'):
        s.rect(1275,245,549,670)
        s.text(1549,289,'OTA CAPTURE',30,True,anchor='middle')
        s.node('tx_node',1374,318,350,64,'USRP N210 TX',size=27)
        s.arrow([(1549,383),(1549,447)])
        s.rect(1569,393,161,36,'white',stroke='none',r=0)
        s.text(1574,419,'over the air',22,color=SECOND)
        s.node('rx_node',1374,453,350,64,'USRP N210 RX',size=27)
        s.arrow([(1549,518),(1549,552)])
        s.node('window_node',1374,558,350,64,'32 ms RF window',size=27)
        s.arrow([(1549,623),(1549,657)])
        s.node('classifier_input_node',1374,663,350,64,'classifier input',size=27)
        s.line(1303,750,1796,750)
        s.text(1303,787,['12.5 MS/s','400,000 complex IQ samples / window','2.437 GHz','2× USRP N210 SDRs'],24,leading=32,id='capture_facts')
    s.save()

def slide05():
    s=Slide(5,'The OSR decision must detect unfamiliar behavior without solving the problem by rejecting too much known data.')
    with s.group('varmax_panel'):
        s.rect(96,250,560,675)
        s.text(124,300,['VARMAX — SCORE-BASED','REJECTION'],29,True)
        for i,label in enumerate(['classifier evidence','unknownness score','threshold','known / unknown']):
            y=392+i*92
            s.node('varmax_'+str(i),176,y,400,60,label,size=26,bold=False)
            if i<3:s.arrow([(376,y+61),(376,y+85)])
        s.text(126,817,'✓ useful unknownness evidence',24,color=GREEN)
        s.text(126,860,'✕ threshold choice can sacrifice known samples',24,color=SECOND,maxw=500)
    with s.group('dqn_style_panel'):
        s.rect(680,250,560,675)
        s.text(708,300,['DQN-STYLE CONFIDENCE','HEAD'],29,True)
        s.node('confidence_state',810,390,300,135,'P1\nP1 − P2\nH(p)',size=26,bold=False)
        s.arrow([(960,526),(960,566)])
        s.node('learned_decision',760,575,400,66,'learned decision',size=26)
        s.arrow([(960,642),(960,688)])
        s.text(960,727,'known / unknown',27,anchor='middle')
        s.text(710,817,'✓ learned decision boundary',24,color=GREEN)
        s.text(710,860,'✕ no explicit guarantee on known rejection',24,color=SECOND,maxw=500)
    with s.group('operating_requirement_panel'):
        s.rect(1264,250,560,675,stroke=BLUE,sw=4)
        s.text(1292,300,['WHAT DEPLOYMENT','ACTUALLY NEEDS'],29,True)
        s.text(1544,440,'Detect unknowns',31,True,anchor='middle')
        s.text(1544,492,'+',36,anchor='middle')
        s.text(1544,548,'Preserve known classifications',28,anchor='middle')
        s.arrow([(1544,573),(1544,624)],BLUE)
        s.node('explicit_budget',1300,639,488,111,'EXPLICIT KNOWN-REJECTION\nBUDGET',BLUE,27)
        s.text(1300,815,'Reject unfamiliar behavior — but only within a controlled known-sample cost.',27,True,maxw=488,leading=34)
    s.save()

def slide06():
    s=Slide(6,"DQNGuard decides whether the classifier's prediction conforms to learned known behavior.")
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/'hero.svg'
        subprocess.run(['pdftocairo','-svg',str(ROOT/'assets/figures/hero_dqnguard_pipeline_s23_tikz.pdf'),str(f)],check=True)
        hero=f.read_text(); m=re.search(r'viewBox="([^"]+)"',hero); _,_,w,h=map(float,m.group(1).split())
        scale=min(1700/w,690/h); x=110+(1700-w*scale)/2; y=245+(690-h*scale)/2
        inner=re.sub(r'^.*?<svg[^>]*>','',hero,flags=re.S).rsplit('</svg>',1)[0]
        # Prefix imported IDs without modifying source artwork or glyph geometry.
        ids=re.findall(r'\bid="([^"]+)"',inner)
        for old in sorted(ids,key=len,reverse=True):
            inner=inner.replace(f'id="{old}"',f'id="s23_{old}"').replace(f'#{old}"',f'#s23_{old}"').replace(f'#{old})',f'#s23_{old})')
        s.add(f'<g id="hero_figure_s23" transform="translate({x} {y}) scale({scale})">{inner}</g>')
    s.save()

def slide07():
    s=Slide(7)
    # Role summary does not route target data into calibration.
    with s.group('role_strip'):
        s.node('surrogate_role',350,238,325,62,'Surrogate: Scan',AMBER,25)
        s.node('target_role',699,238,310,62,'Target: Sustain',RED,25)
        s.node('known_role',1033,238,537,62,'Known: Burst / Hop / Replay',GREEN,25)
    # Connectors behind nodes. Green paths originate exclusively at known calibration.
    with s.group('role_connectors'):
        s.arrow([(960,430),(960,455),(585,455),(585,480)])
        s.arrow([(960,455),(1335,455),(1335,480)])
        s.arrow([(585,605),(585,628),(850,628),(850,640)],GREEN)
        s.arrow([(1335,605),(1335,628),(1070,628),(1070,640)],AMBER)
        s.arrow([(350,545),(315,545),(315,837),(380,837)],GREEN)
        s.arrow([(585,605),(585,765),(1285,765),(1285,785)],GREEN)
        s.arrow([(635,885),(635,899),(800,899),(800,905)],GREEN)
        s.arrow([(1285,885),(1285,899),(1120,899),(1120,905)],GREEN)
    s.node('backbone_node',730,320,460,110,'3-class PA backbone\nBurst | Hop | Replay',size=29)
    s.node('known_calibration_node',350,485,470,120,'KNOWN CALIBRATION\nBurst • Hop • Replay',GREEN,26)
    s.node('surrogate_calibration_node',1100,485,470,120,'SCAN SURROGATE\nwithheld from backbone training',AMBER,25)
    s.node('dqn_fit_node',730,645,460,105,'FIT DQN CONFIDENCE HEAD\nknown + surrogate states',BLUE,25)
    s.node('known_guard_fit_node',385,790,500,95,'FIT GUARD BANDS ON KNOWN ONLY',GREEN,25)
    s.node('known_threshold_node',1035,790,500,95,'SET 5% THRESHOLD ON KNOWN ONLY',GREEN,25)
    s.node('final_evaluation_node',570,910,780,90,'FINAL EVALUATION:\nknown test + Sustain target unknown',RED,26)
    s.text(960,1027,'Scan surrogate is not included in final test metrics.',21,color=SECOND,anchor='middle')
    s.save()

def slide08():
    s=Slide(8)
    with s.group('experiment_strip'):
        s.rect(96,225,1728,92,PANEL,stroke='none')
        s.text(120,261,'Fixed-surrogate comparison • Scan surrogate • targets: Burst / Sustain / Hop / Replay',26,True)
        s.text(120,296,'mean ± SD across four held-out target folds',24,color=SECOND)
    # Domain expanded slightly from the suggested range to show every full SD bar.
    x0,y0,pw,ph=225,825,945,420
    X=lambda v:x0+v/.18*pw
    Y=lambda v:y0-(v-.48)/.55*ph
    with s.group('operating_plot'):
        s.rect(X(0),Y(1.03),X(.065)-X(0),Y(.82)-Y(1.03),TINT[GREEN],stroke='none',r=0,id='desirable_region')
        s.text(225,367,'Unknown F1 → higher is better',27,True)
        with s.group('axes'):
            for v in [.5,.6,.7,.8,.9,1.0]:
                s.line(x0,Y(v),x0+pw,Y(v),BORDER,1)
                s.text(205,Y(v)+7,f'{v:.2f}',22,color=SECOND,anchor='end')
            for v in [0,.03,.06,.09,.12,.15,.18]:
                s.line(X(v),y0,X(v),y0+8,INK,2)
                s.text(X(v),858,f'{v:.2f}',22,color=SECOND,anchor='middle')
            s.line(x0,Y(1.03),x0,y0,INK,2)
            s.line(x0,y0,x0+pw,y0,INK,2)
            s.text(697,908,'Known rejection → lower is better',27,True,anchor='middle')
        points=[('dqnguard_point',.050,.865,.004,.142,BLUE,'DQNGuard',570,485),('dqn_ids_point',.063,.701,.017,.197,GRAY,'DQN-IDS-style head',600,740),('varmax_point',.128,.745,.043,.146,GRAY,'VarMax surrogate-all',850,654)]
        with s.group('error_bars'):
            for _,x,y,dx,dy,*_ in points:
                s.line(X(x-dx),Y(y),X(x+dx),Y(y),GRAY,2)
                s.line(X(x),Y(y-dy),X(x),Y(y+dy),GRAY,2)
                for xx in [X(x-dx),X(x+dx)]:s.line(xx,Y(y)-6,xx,Y(y)+6,GRAY,2)
                for yy in [Y(y-dy),Y(y+dy)]:s.line(X(x)-6,yy,X(x)+6,yy,GRAY,2)
        for id,x,y,dx,dy,c,label,lx,ly in points:
            with s.group(id):
                s.add(f'<circle cx="{X(x)}" cy="{Y(y)}" r="{12 if c==BLUE else 9}" fill="{c}" stroke="white" stroke-width="3"/>')
                s.text(lx,ly,label,26,True,c if c==BLUE else INK)
                s.text(lx,ly+29,f'{y:.3f} F1 · {100*x:.1f}% known rejection',22,color=SECOND)
        s.text(120,965,'Error bars = SD across held-out target folds, not rerun variance.',22,color=SECOND)
    with s.group('interpretation_rail'):
        with s.group('auroc_card'):
            s.rect(1300,345,524,245)
            s.text(1330,389,'AUROC / RANKING',29,True)
            for y,label,val in [(447,'VarMax','0.951'),(500,'DQNGuard','0.891'),(553,'DQN-IDS-style','0.829')]:
                s.text(1330,y,label,27); s.text(1790,y,val,30,True,anchor='end')
        s.text(1320,647,'Ranking quality ≠ usable thresholded decision',30,True,maxw=480,id='ranking_callout')
        with s.group('osr_f1_card'):
            s.text(1320,761,'OSR macro F1:',29,True,BLUE)
            s.text(1320,808,'0.881 ± 0.109',40,True,BLUE)
            s.text(1320,855,'DQNGuard combines the highest mean Unknown F1 with the lowest mean known rejection in the main comparison.',25,maxw=480,leading=31)
    s.save()

def slide09():
    s=Slide(9,'Rotating both the target unknown and surrogate-open class reveals strong, directional calibration dependence.')
    s.image('target_surrogate_matrix_asset',250,235,1420,610)
    with s.group('interpretation_strip'):
        # Tight 20 px secondary lines preserve all locked labels in the 120 px strip.
        for x,id in [(96,'target_variation'),(680,'best_surrogate_changes'),(1264,'pair_failure')]:
            with s.group(id):
                s.rect(x,865,560,120,PANEL,stroke='none',r=12)
                heading={'target_variation':'TARGET VARIATION','best_surrogate_changes':'BEST SURROGATE CHANGES','pair_failure':'SOME PAIRS NEARLY FAIL'}[id]
                s.text(x+18,891,heading,24,True)
                if id=='target_variation':
                    s.text(x+18,929,'Slide 8: 0.865 ± 0.142',27,True)
                    s.text(x+18,965,'Across target PAs — not repeated runs',22)
                elif id=='best_surrogate_changes':
                    s.text(x+18,917,'Scan → Hop    Burst → Replay',22)
                    s.text(x+18,944,'Sustain / Hop / Replay → Scan',22)
                    s.text(x+18,972,'No universal surrogate',22,True)
                else:
                    s.text(x+18,925,'Unknown F1 ≈ 0 in several cells',24,True)
                    s.text(x+18,951,'Mismatched calibration evidence may not transfer',22,maxw=524,leading=25)
    s.save()

def slide10():
    s=Slide(10,'Can we choose a good surrogate before the true unknown has ever been observed?')
    for x,id in [(96,'calibration_performance_card'),(680,'confidence_geometry_card'),(1264,'feature_geometry_card')]:
        with s.group(id):
            s.rect(x,275,560,560)
            if x==96:
                s.text(x+28,320,['SURROGATE CALIBRATION','PERFORMANCE'],29,True)
                s.text(x+28,418,'“If I reject the surrogate well, will I reject the true unknown well?”',26,maxw=504)
                s.text(x+28,575,'ρ ≈ −0.075',70,True)
                s.text(x+28,625,'Pearson r ≈ −0.047',26)
                s.text(x+28,672,'Best surrogate selected: 2 / 5 targets',25)
                s.text(x+28,744,'Rejecting the surrogate well does not imply transfer.',27,True,maxw=504)
            elif x==680:
                s.text(x+28,320,'CONFIDENCE GEOMETRY',29,True)
                s.text(x+28,418,'P1 • P1−P2 • entropy',26,color=SECOND)
                s.text(x+28,575,'ρ ≈ −0.552',70,True)
                s.text(x+28,710,'The intuitive confidence-space rule pointed in the wrong direction overall.',27,True,maxw=504)
            else:
                s.text(x+28,320,'FEATURE GEOMETRY',29,True)
                s.text(x+28,500,'best simple +ρ ≈',30,True)
                s.text(x+28,575,'+0.406',78,True)
                s.text(x+28,672,'Best surrogate selected: 1 / 5 targets',25)
                s.text(x+28,744,'Some positive signal exists, but proximity alone is not reliable.',27,True,maxw=504)
    with s.group('shared_conclusion'):
        for x in [376,960,1544]:s.arrow([(x,839),(x,870)])
        s.rect(300,875,1320,105,INK,stroke=INK)
        s.text(960,917,'NO RELIABLE SINGLE-SURROGATE SELECTION RULE',34,True,'white',anchor='middle')
        s.text(960,956,'Good surrogate performance does not imply good target transfer.',26,color='white',anchor='middle')
    s.save()

def slide11():
    s=Slide(11,'In VarMax, surrogates change calibration parameters; in DQNGuard, the surrogate changes the learned open-set decision function itself.')
    s.line(933,245,933,730)
    with s.group('varmax_surrogate_all_group'):
        s.text(96,277,'ORIGINAL CONTRIBUTION — VARMAX SURROGATE-ALL',24,True)
        s.node('frozen_backbone',280,304,452,60,'ONE FROZEN BACKBONE',size=26)
        for x,name in [(246,'Scan'),(506,'Burst'),(766,'Hop …')]:
            s.arrow([(506,365),(506,386),(x,386),(x,410)])
            s.node('pseudo_'+name.split()[0].lower(),x-90,418,180,77,name+'\npseudo open',AMBER,24)
            s.arrow([(x,496),(x,519),(506,519),(506,537)],AMBER)
        s.text(506,564,'threshold / band candidates',26,anchor='middle')
        s.arrow([(506,576),(506,602)])
        s.text(506,631,'ALL CANDIDATES COMPETE',28,True,anchor='middle')
        s.arrow([(506,642),(506,664)])
        s.text(506,693,'SELECT ONE RULE',28,True,anchor='middle')
        s.text(96,734,'Surrogate-all is a calibration search, not a deployed ensemble.',23,True)
    with s.group('dqnguard_mismatch_group'):
        for y,name,suffix in [(295,'Scan','A'),(395,'Burst','B'),(495,'Hop','C')]:
            s.node('surrogate_'+suffix,980,y,330,70,name+' surrogate',AMBER,27)
            s.arrow([(1320,y+35),(1400,y+35)])
            s.node('dqn_'+suffix,1410,y,250,70,'DQN '+suffix,BLUE,29)
        s.arrow([(1680,330),(1710,330),(1710,593),(1420,593),(1420,612)],BLUE)
        s.line(1660,430,1710,430,BLUE,4);s.line(1660,530,1710,530,BLUE,4)
        s.text(980,644,'DIFFERENT LEARNED SCORE SPACES',28,True,BLUE)
        s.text(980,678,'Thresholds are not directly interchangeable across separately fitted DQNs.',24,True,maxw=844,leading=28)
        s.text(980,735,'Current DQNGuard also withholds its external surrogate from the backbone taxonomy.',21,maxw=844,leading=25)
    s.text(96,797,'FUTURE WORK — NOT YET EVALUATED',23,True,PURPLE,id='future_work_tag')
    with s.group('future_architectures'):
        for x,id,head,body in [(96,'pooled_dqn_card','POOLED MULTI-SURROGATE DQN','A + B + C surrogate states\n→ ONE DQN → one score space'),(684,'dqn_ensemble_card','SURROGATE-SPECIFIC DQN ENSEMBLE','DQN A + DQN B + DQN C\n→ normalize / aggregate'),(1272,'hybrid_guard_card','HYBRID VARMAX / DQNGUARD','multi-surrogate deterministic guard evidence + one DQN signal')]:
            with s.group(id):
                s.rect(x,805,552,175,TINT[PURPLE],PURPLE)
                s.text(x+24,850,head,24,True,PURPLE,maxw=504,leading=28)
                s.text(x+24,918,body,25,maxw=504,leading=30)
    s.text(96,1008,"Goal: reduce dependence on a favorable single surrogate while preserving DQNGuard's strong thresholded operating point and explicit 5% known-rejection budget.",21,maxw=1728,leading=24)
    s.save()

def slide12():
    s=Slide(12)
    for x,id,head in [(96,'takeaway_1_group','1. USABLE OPEN-WORLD OPERATING POINT'),(680,'takeaway_2_group','2. SURROGATE TRANSFER IS TARGET-DEPENDENT'),(1264,'takeaway_3_group','3. MULTI-SURROGATE DQNGUARD')]:
        with s.group(id):
            s.rect(x,250,560,610)
            s.text(x+28,297,head,29,True,maxw=504,leading=35)
            if x==96:
                for y,num,label,mid in [(420,'0.865','UNKNOWN F1','metric_unknown_f1'),(535,'0.881','OSR MACRO F1','metric_osr_f1'),(650,'0.050','KNOWN REJECTION','metric_known_reject')]:
                    with s.group(mid):
                        s.text(x+28,y,num,78,True,BLUE)
                        s.text(x+274,y-8,label,23,True)
                s.text(x+28,708,'Best thresholded operating point in the main comparison',24,True,maxw=504,leading=30)
                s.text(x+28,793,'Preserve known PA evidence while exposing unfamiliar RF behavior.',26,maxw=504,leading=32)
            elif x==680:
                s.image('matrix_thumbnail',828,361,264,215)
                s.text(x+28,616,'20 ordered target–surrogate pairs',29,True)
                s.text(x+28,660,['Best surrogate changes with the target','Several mismatched pairs approach F1 ≈ 0','No simple target-blind selector was reliable'],23,leading=34)
                s.text(x+28,793,'Calibration transfer is directional and behavior dependent.',26,True,maxw=504,leading=32)
            else:
                s.text(x+280,402,'VarMax surrogate-all philosophy',25,anchor='middle',id='varmax_node')
                s.text(x+280,446,'+',32,anchor='middle')
                s.text(x+280,490,'DQNGuard budgeted decision layer',25,anchor='middle',id='dqnguard_node')
                s.arrow([(x+280,510),(x+280,548)],PURPLE,id='merge_arrow')
                s.node('future_node',x+28,563,504,83,'MULTI-SURROGATE DQNGUARD?',PURPLE,27)
                s.text(x+28,686,'FUTURE WORK — ARCHITECTURAL REDESIGN REQUIRED',21,True,PURPLE,maxw=504,leading=26)
                s.text(x+28,753,"Goal: retain DQNGuard's Unknown F1, OSR macro F1, and explicit known-rejection budget while reducing single-surrogate dependence.",24,maxw=504,leading=29)
    with s.group('scope_footer'):
        s.line(96,895,1824,895)
        s.text(96,931,'Preliminary Actions are RF precursor evidence. DQNGuard routes evidence; it does not make the final attack attribution or response decision.',25,maxw=1728,leading=31)
    s.text(960,1015,'Questions?',34,True,anchor='middle',id='questions_label')
    s.save()

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    for n in range(1,13):
        globals()[f'slide{n:02}']()
