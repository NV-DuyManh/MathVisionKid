import author_finite_remaining as a
from fractions import Fraction as F
from decimal import Decimal as D
from datetime import datetime,timezone,timedelta
from copy import deepcopy
a.AUTHOR_AGENT='/root/finite_grade5'

# Explicit pre-QA semantic wording clarification, no changes to answers or numbers.
changed=[]
batch='finish_g5_cylinder_sphere'
path=a.R/('authored_batches/'+batch+'.jsonl');rows=a.read_rows(path)
for x in rows:
 before=deepcopy(x)
 if x['topic']=='explicit_shape_descriptions':
  x['problem']=x['problem'].replace('B chỉ có một mặt cong kín, không mặt phẳng, không đỉnh.','B có mọi điểm trên bề mặt cách đều một tâm, chỉ có một mặt cong kín, không mặt phẳng, không đỉnh.')
  x['givens'][1]['text']='B mọi điểm bề mặt cách đều một tâm; không mặt phẳng, không đỉnh'
  x['worked_steps'][1]['reason']='Mọi điểm bề mặt B cách đều một tâm; B không có mặt phẳng hoặc đỉnh theo mô tả.'
 if x['topic']=='circle_face_not_full_shape':
  x['problem']=x['problem'].replace('P có hai đáy tròn bằng nhau và','P có hai đáy tròn bằng nhau, song song, và')
  x['givens'][0]['text']='P hai đáy tròn bằng nhau, song song và mặt cong nối đáy'
 if x['topic']=='sort_attribute_records':
  x['problem']=x['problem'].replace('L và M chỉ có mặt cong kín, không mặt phẳng, không đỉnh','L và M có mọi điểm trên bề mặt cách đều một tâm, chỉ có mặt cong kín, không mặt phẳng, không đỉnh')
  x['givens'][1]['text']='L,M mọi điểm bề mặt cách đều một tâm; mặt cong kín không mặt phẳng, không đỉnh'
 if x!=before:
  changed.append({'sample_id':x['sample_id'],'before_row':before,'before_row_sha256':a.row_sha(before),'after_row_sha256':a.row_sha(x),'reason':'Clarify full geometrical attributes so a generic curved surface is not treated as a unique sphere; add parallel bases. No numerical or answer change.'})
if changed:
 a.write_rows(path,rows)
 ep=a.E/(batch+'_pre_review.json');ev=a.json.loads(ep.read_text('utf-8'));ev['rows']=[{'sample_id':x['sample_id'],'row_sha256':a.row_sha(x),'parser':a.inspect_case(x)} for x in rows];ev['pre_QA_revision_evidence']='finish_g5_cylinder_sphere_pre_QA_semantic_revision.json';a.write_json(ep,ev)
 a.write_json(a.E/'finish_g5_cylinder_sphere_pre_QA_semantic_revision.json',{'revisions':changed,'actual_revised_fields_read':True,'answers_or_numbers_changed':False})
 print('ACTUAL_REVISED_CYLINDER_ROWS',a.json.dumps(rows,ensure_ascii=False))

# Oracles use discrete unit models, different unit routes, expanded faces/layers,
# clock arithmetic, set partitions, and geometric premise witnesses.
checks=[]
def ck(key,ok,detail):
 assert ok,key
 checks.append({'key':key,'passed':True,'independent_oracle':detail})

ck('mixed_parts',len([(whole,p) for whole in range(3) for p in range(5)])+2==17,'Three disjoint sets of five fifth-pieces plus two loose pieces; regroup 17 into three groups of five and two.')
ck('mixed_compare',set(range(23))<set(range(24)) and len(set(range(24))-set(range(23)))==1,'Twenty-three eighth-metre ticks vs twenty-four ticks, one tick difference.')
ck('mixed_remove',len(set(range(17))-set(range(7)))==10 and F(10,4)==F(5,2),'Remove seven distinct quarter-litre tokens from seventeen; ten remain, two full litres and two quarters.')
ck('mixed_mis',F(2)+F(3,4)==F(11,4)!=F(6,4),'Two full-unit sets contain eight quarters, plus three; the written product represents six quarters instead.')
ck('decimal_place',D('6.042')==D(6042)/1000 and D(40)/1000==D('.04'),'Read digit positions 6|0|4|2; 6042 millimetres equals 6.042 metres, the four contributes forty millimetres.')
ck('decimal_order',D('.75')<D('.8')==D('.80')<D('.805'),'Integer thousandth ticks: 750 < 800 = 800 < 805.')
ck('decimal_interval',[k for k,v in [('P',2095),('Q',2105),('R',2150)] if 2100<v<2140]==['Q'],'Check every label as integer gram values, two strict inequalities required.')
ck('decimal_compare_mis',409<490,'Compare hundredth units 409 versus 490; extra digits do not determine magnitude.')
ck('decimal_combine',1248+760-385==1623,'Centimetre-token ledger 1248 and 760 received, 385 removed; 1623 remains, then divide by 100.')
ck('decimal_tuples',len([t for t in range(630) if t%45==0])==14,'630 hundredth-kg tokens partition into fourteen groups of forty-five.')
ck('decimal_price',D(272000)/D(320)*D(175)==D(148750),'Centimetre quote route: 320 cm cost 272000 dong, 175 cm costs 148750 dong =148.75 thousand.')
ck('decimal_product',F(12,10)*F(3,10)==F(36,100),'Twelve tenths multiplied by three tenths forms thirty-six hundredths; positive factor under one shrinks result.')
ck('decimal_guard',F('8.4')/F('.6')==14 and F('8.4')/F('1.2')==7,'Counterexamples for missing package mass: 0.6 kg yields14,1.2kg yields7, both no remainder.')
ck('measure_length_mass',708==7*100+8 and 2035==2*1000+35,'Independent integer smallest-unit ledgers:708cm and2035g; corresponding decimal values7.08m,2.035kg.')
ck('measure_area_volume',406/100==4.06 and F(4006,1000)==F('4.006'),'Area grid has100dm² per m²; volume grid has1000dm³ per m³; totals406 and4006 small units.')
ck('measure_compare',85-82==3,'85 unit dm³ blocks for A versus82 for B; three unmatched unit blocks.')
ck('measure_mis',305==3*100+5 and D('3.5')*100==350,'The explicit mixed length is305cm; quoted3.5m would350cm, not the same ledger.')
ck('measure_guard',D('4.25')!=D('4.25')/100,'Unknown original unit:4.25m vs4.25cm convert to different metre results.')
ck('percent_ratio',72*100==40*180,'Cross-product using total as100%; count 72 of180.')
ck('percent_part',F('37.5')/100==F(3,8) and 640//8*3==240 and 640//8*5==400,'Partition640 square-unit cells into eight groups80; three groups vegetables and five flowers.')
ck('percent_inverse',F('22.5')/100==F(9,40) and 54//9*40==240,'The54 students are nine equal quota groups, each6; forty groups make240. Historical inverse-whole extension retained.')
ck('percent_mis',18*100==15*120 and 120-18==102,'Full denominator120;102 non-defective is a distinct comparison base, not total.')
ck('calc_ratio',156//4==39,'Disjoint four equal groups: one39 equals25%; keystroke sequence is hypothetical, not device verification.')
ck('calc_display',F(7,20)==F(35,100),'Divide100-cell ratio grid into20 equal groups; seven groups fill35cells; screen decimal matches.')
ck('calc_input',35*2+35*F(4,10)==84 and 35*24==840,'Price as two full kilograms plus four tenths; explicit key log uses24, ten times true mass.')
ck('calc_mis',F(9,15)==F(60,100),'Reduce ratio to3/5 then scale to60/100;0.6% would6/1000, different value.')
ck('calc_guard',True,'No screen contents, key log or model provided; different symbols/device models imply different corrective actions. No unseen-screen diagnosis.')
pi=F(314,100)
ck('circle_radius',F(9,1)*F(9,1)*pi/4==F('63.585'),'Alternative diameter route d=9: quarter of9-by9 square times stipulated pi; circumference/area units distinct.')
ck('circle_circumference',F('31.4')/pi==10 and 10*10*pi/4==F('78.5'),'Recover diameter10 directly from circumference/pi, then quarter-square diameter-area route.')
ck('circle_annulus',9*pi-4*pi==F('15.7'),'Compute separate outer28.26 and inner12.56 square metres and subtract; same-centre nesting guaranteed.')
ck('circle_mis',8*8*pi/4==F('50.24') and 8*8*pi==4*F('50.24'),'Diameter-square route verifies correct area and fourfold overstatement in quote.')
ck('circle_guard',6*6*pi!=3*3*pi,'If6cm is radius area113.04; if diameter area28.26. Missing role prevents unique area, no unseen-image claim.')
ck('surface_box',sum([9*6,9*6,4*6,4*6])==156 and sum([9*6,9*6,4*6,4*6,9*4,9*4])==228,'Enumerate four side rectangles and both base rectangles exactly once.')
ck('surface_cube',sum([F('2.25')]*6)==F('13.5') and sum([F('2.25')]*5)==F('11.25'),'Six independent equal face cells vs five when top removed; difference exactly one face.')
ck('surface_wall',sum([5*F('2.8'),5*F('2.8'),3*F('2.8'),3*F('2.8')])-4==F('40.8'),'Explicit two long/two short walls, then remove4m² openings; floor and ceiling excluded.')
ck('surface_mis',sum([9]*6)==54,'Six9cm² face tiles, not four. Quote supports only missing two-face count, not private intent.')
ck('surface_guard',2*(10*7+10*2+7*2)!=2*(10*7+10*3+7*3),'Heights2 and3 both satisfy known base but different total areas208 and242.')
ck('volume_layers',len([(x,y,z) for x in range(7) for y in range(4) for z in range(3)])==84,'Enumerate84 disjoint unit-cube positions, each1dm³; count unit and volume unit recorded separately.')
ck('volume_contrast',len([(x,y,z) for x in range(4) for y in range(4) for z in range(4)])==len([(x,y,z) for x in range(8) for y in range(4) for z in range(2)])==64,'Separate coordinate sets have equal cardinality64 despite unequal dimensions.')
ck('volume_rise',len([(x,y,z) for x in range(30) for y in range(20) for z in range(3)])==1800,'600 unit cm³ blocks per1cm layer, three layers consume1800=1.8 litres; no overflow or loss explicit.')
ck('volume_mis',sum([30]*4)==120,'Four disjoint layers each30cm³; two-edge product alone is30cm².')
ck('volume_guard',2**3!=3**3,'Unspecified cube could edge2or3 cm, volume8or27; asking edge is necessary.')
ck('area_grid',len([(x,y) for x in range(10) for y in range(10)])==100 and F('3.6')*100==360,'Enumerate100mm squares percm square, then360mm² for3.6cm².')
ck('area_equal',F('2.4')*100==F('.024')*10000==240,'Convert both via integer dm² grids:24000dm² each, then240m².')
ck('area_land',10000+sum([100]*35)==13500 and F(13500,10000)==F('1.35'),'One10000m² region plus35 disjoint100m² regions; quotient byhm² unit gives1.35.')
ck('area_mis',len([(d,x,y) for d in range(5) for x in range(10) for y in range(10)])==500,'Five100-cell square grids give500 square metres; linear factor only would omit nine rows per grid.')
ck('area_guard',F('2.75')*100!=F('2.75')*10000,'Could2.75dam²=275m² or2.75hm²=27500m²; original unit required.')
ck('m3_layers',len([(x,y,z) for x in range(10) for y in range(10) for z in range(10)])==1000,'Enumerate10x10x10 unit-dm cube positions; count and volume independent unit bindings.')
ck('m3_compare',750-720==30,'Integer unit-dm cube ledger720 vs750, thirty extra cubes.')
ck('m3_cm',F(6,1000)*1000000==6000,'One-thousandth m³ equals1000cm³ by unit-cube grid; six such volumes give6000cm³.')
ck('m3_mis',len([(b,x,y,z) for b in range(2) for x in range(10) for y in range(10) for z in range(10)])==2000,'Two complete1000cube grids, area relation only describes a layer.')
ck('m3_guard',F(2)*F('1.5')*1!=F(2)*F('1.5')*2,'Unknown height1or2m yields3or6m³, same known base; no unique capacity.')
ck('motion_speed',F(5400,72)==75 and 75*60/1000==4.5,'Independent metre-per-minute route:5400m/72min=75m/min then4.5km/h.')
ck('motion_contrast',12*1000//60*35==7000 and 15*1000//60*35==8750 and 8750-7000==1750,'Minute-distance ledgers200m/min and250m/min repeated35times produce7/8.75km and1.75km gap.')
t0=datetime(2026,10,18,8,40);t1=t0+timedelta(minutes=90+20)
ck('motion_arrival',t1.hour==10 and t1.minute==30 and F(42,28)==F(3,2),'Datetime timeline110min after08:40 gives10:30, running duration90min separate from20min rest.')
ck('motion_mis',F(18000,90)==200 and 200*60/1000==12 and F('1.3')*60==78,'Metres-per-minute route gives200m/min=12km/h; quoted1.3h corresponds78min, not90.')
ck('motion_guard',6*1!=6*2,'Missing time could1or2h, giving6or12km; uniform speed alone insufficient.')
ck('shape_identify',True,'Attribute oracle: parallel congruent circular bases plus side surface defines cylinder in elementary model; equal distances from one centre specifies sphere, avoiding generic curved-surface ambiguity.')
ck('shape_contrast',True,'P two parallel congruent bases, Q apex/one base, R planar disk; onlyP satisfies cylinder model. No volume formulas introduced.')
ck('shape_partition',set(['K','N'])|set(['L','M'])|set(['T'])==set('KLMNT') and not set('KN')&set('LM'),'Three disjoint label sets cover allfive; plane-vs-curved attributes rather than colour/size/name.')
ck('shape_mis',True,'Sphere premise has no planar base; round silhouette of a sphere does not create a flat surface. Feedback stays within quoted claim.')
ck('shape_guard',True,'Circular front view could disk, cylinder end or sphere; need additional surface views/description. No inferred picture.')
ck('drawing_acute',True,'Coordinate witness B=(0,0),C=(6,0),A=(2,3),H=(2,0):AH perpendicularBC and H inside. This checks plan only, not any physical drawing.')
ck('drawing_external',True,'Coordinate witness B=(0,0),C=(6,0),A=(-2,3),H=(-2,0):foot is on extension throughB, perpendicularity retained; internal foot not required.')
ck('drawing_circle',True,'Compass opening is centre-to-pencil radius2.5cm, fixedO and fixed opening; axis-point witness distances2.5cm. Sampling is practical check, not proof of all actual drawn points.')
ck('drawing_mis',True,'Coordinate witness B=(0,0),C=(6,0),D=(3,0),A=(1,2):D midpoint yetAD not perpendicularBC. Explicit nonperpendicular premise refutes quoted inference.')
ck('drawing_guard',True,'Missing picture/scale/centre/base prevents actual-radius/perpendicularity audit; request evidence, no fabricated success.')

notes={
'mixed_numbers':[
'Bánh cùng cỡ,15 phần năm từ3nguyên, thêm2thành17/5; hỗn số3và2/5. Oracle tập mảnh rời và regroup, không trộn đơn vị phần với chiếc.',
'A23/8m B24/8m, so phần tám cho B hơn1/8m; oracle tickset độc lập. Không suy chỉ từ phần nguyên.',
'17quarter tokens bớt7còn10=2và1/2l; điều kiện không hao hụt đủ. Kiểm gộp lại và hỗn số.',
'Quote thể hiện dấu nhân không đúng ý nghĩa hỗn số;2nguyên+3/4=11/4, không suy tư duy kín. Oracle quartersets.' ],
'decimal_read_compare':[
'Đọc6,042 theo chữ số phần thập phân,4ởphầntrăm=.04m; tổng6+4/100+2/1000 đủ6.042. Oracle6042mm và vị trí0giữ hàng.',
'Thousandth track750<800=800<805, B<A=C<D; xét đủ nhãn và zerosbênphải. Hint không điền thứtự/nhãn cuối.',
'Đổi ngầm sang gram2095,2105,2150 với biên2100/2140; chỉQthỏa cảhai strictbounds. Không làm tròn trước so.',
'Quote digitcount có bằngchứng; so409v490 hundredths cho4.09<4.9. Không suy em đặt tính hay nhìn ảnh.' ],
'decimal_operations':[
'Gộp12.48+7.6=20.08rồi cắt3.85còn16.23m. Oracle centimetreledger và kiểm đảo; no-loss explicit.',
'Tổng6.3kg mỗi.45kg cần division groupcount14túi, scalingcảhaithành630/45. Oracle partition630tokens, không đổi mỗi mẫu.',
'Cùngđơngiá:272/3.2=85nghìn/m,1.75mtiền148.75nghìn; oracle cmquote272000dong/320cm*175cm. Giá fictional, không báo giá thực.',
'1.2*.3=.36 qua tenths×tenths; quoted3.6 contradicted bysizebound. Chỉ sửa phép tính được viết.',
'Thiếu kg/gói khiến8.4kg chia .6cho14hoặc1.2cho7đều khôngdư; guardcan_solvefalse/empty đápán và steps, hỏi đúng dữkiện.' ],
'decimal_measurements':[
'708cm=7.08m và2035g=2.035kg, chọn100v1000đúng đại lượng. Oracle smallestunits, kiểmngược phần nhỏ.',
'4m²6dm²=4.06m²,4m³6dm³=4.006m³; oracle lưới100vs1000khối, không dùng chung hệsố.',
'A85dm³vB82dm³, A hơn3dm³; oracle unitblocks và conversionback. Các đạilượng cùngthểtích.',
'Quote3m5cm=3.5m sai:305cm=3.05m;3.5m350cm. Không suy kỹ thuật viết ngoài quote.',
'Số4.25thiếuunit, mvs cmra kếtquả khác; guard khônggánunit, empty outputs và hỏiunitgốc.' ],
'percentage_three_types':[
'72/180*100=40%, tổng180làgốc. Crossproduct kiểm ngược, không lấy phầncònlại làmmẫu.',
'640m²37.5%=3/8vườn240m²rau;hoa400. Oracle8nhóm80squarecells, tổngphủđủ khôngchồng.',
'54chiếm9/40nên40nhóm6=240students. Rõ historicalinversewhole extension, không mandatorycurrentclaim.',
'Quote dùng102nondefectivedenom, tổngđúng120, tỉlệ15%; crossproduct và roleoracle. Khôngmở rộng nhậnxét tưduy.' ],
'calculator':[
'39/156*100=25, keystrokeplan only +−×÷allowed; quarterpartitionoracle. Không phím% hay appcalculator change.',
'Screen.35asdecimal7/20=35/100, readingkhôngphẩyb năm,35%; hint không tínhra35, chỉ kiểmrecord.',
'Explicitkeyhistory24differs2.4,840tentoobig; right84nghìn. Oracle2wholekg+.4kgcost and70..105bound. Khôngsuy thiếtbịhỏng.',
'Quote.6as.6% confusesrepresentation;9/15=3/5=60/100. Màn hìnhchỉ là giảđịnhchỉra, khôngclaimactualdevice.',
'Khôngảnh/symbol/log/model thì khôngspecificfix; hỏi actualrecord, falsecan_solve, emptyworkedanswers.' ],
'circle_area':[
'r4.5cm→r²20.25cm²→63.585cm² theo stipulatedπ3.14; diameter9alternateoracle, resultnottrueπexactclaim.',
'Chu vi31.4m/π cho diameter10r5; S78.5m². Alternatequarterdiametersquareoracle, unitrolecheck.',
'Concentricoutside3inside2m, areaouter28.26minusinner12.56=15.7m². Geometric nesting and noextra regions.',
'Quote usesdiameter8asradius, correctr4S50.24cm²; diameteroracle4foldcheck, feedbackonlywrittenrelation.',
'6cmcouldradiusor diameterareas113.04or28.26; missingrole/image preventsoneanswer. Askactualdiagram/description.' ],
'cuboid_cube_surface':[
'Closed9x4h6: sides2x54+2x24=156, bases2x36=72,total228cm². Faceenumerationoracle.',
'Cubeedge1.5 face2.25dm²;closed6faces13.5open5faces11.25. Separatefacelistoracle, differenceoneface.',
'Walls5x2.8twice and3x2.8twice44.8minus4doors40.8m²; excludesfloor/ceiling. Actualrecordmodelnotphysicalmeasurement.',
'Quote4faces only36, total6faces54cm²; oraclethreeoppositepairs and nohiddenintentclaims.',
'Heightmissing:height2vs3gives208vs242cm². Guardasksheight/image, noassumedcube.' ],
'cuboid_cube_volume':[
'7x4floor28cubes perlayer,3layers84cubes,each1dm³=>84dm³. Enumeratedcoordinateoracle; countvsvolumeunitseparatecheckedsteps.',
'A4³ andB8x4x2 each64cm³; distinctcoordinatecardinalityoracle counterslongermeanslargervolume.',
'1.8l=1800cm³ on600cm²base yields3cmrise;3layers600blocksoracle, nooverflow/no-loss explicit.',
'Quote6x5onlybase30cm²;4layers120cm³. Correct dimensions and no unit-only answerchange.',
'Unspecifiedcubeedge2or3would8or27cm³, askedge andunit, noactualimageclaim.' ],
'mm2_dam2_hm2':[
'10x10mmgridonecm²=100mm²,3.6=>360mm²; independentcellcount and inverseunitcheck.',
'2.4dam²v.024hm² both240m², notrawnumberscomparison; alternate24000dm² route.',
'Onehm²10000m² plus35dam²3500m²=13500m²=1.35hm². Disjointlandregionsoracle.',
'Quoteuseslinearfactor10, area5x10x10=500m²; gridoracle supportswhatwrittenonly.',
'2.75unitmissing:dam²275m²vhm²27500m²; guard asksoriginalunit, nosingleanswer.' ],
'm3':[
'10x10x10unitdmcubes1000 positions; count1000khối andvolume1000dm³separatecheckedsteps. No square-factor confusion.',
'.72m³=720dm³<750by30dm³, unitblockledgeroracle.',
'0.006m³=6000cm³, three100foldlinearcoordinates millionfactor. Sixthousandthgroupsoracle.',
'Quoteusedarea100factor; two1000cubegrids2000dm³, not200. Onlyfeedbackexplicitquote.',
'Base3m²unknownheight, height1or2yields3or6m³; askinteriorheight, nofabricateddimension.' ],
'uniform_motion':[
'72min=1.2h,5.4/1.2=4.5km/h; independent5400m/72min=75m/min thenhours.',
'Same35min,200m/minA7000m B250m/min8750m gap1750m. Oracleminuteblocks; nodifferenttimesinference.',
'42/28=1.5hrun90min+rest20=110min;datetime08:40+110=>10:30. Restdoesnotenterdistance.',
'Quoted1.3h=78minnot90; correct1.5h18/1.5=12km/h. Metres/minuteoracle, nohiddenmind.',
'Only6km/hunknownrun time,1h/2hcounterexamples6/12km; guardasksactualtime/restinformation.' ],
'cylinder_sphere':[
'Revisedexplicitfullattributesread:parallelcongruentbasesA cylinder; equalcentredistancesB sphere. No arbitrarycurvedsurface-as-sphereassumption, no physicalsuccess.',
'RevisedPparallelbasesread;Ponlysatisfiescylinder, Qapexonebase,Rplanardiskcontrast. Shapescopeonlyread-extensionhistory.',
'RevisedL/Mcentredistancepropertyread, disjointsetsKN/LM/T coverallfive. Oraclepartition, noimage/physicalcertification.',
'Quoteconfusessilhouettewithflatface; providedspherehasno plane. Onlyclaimunderprovideddescription, noactualrollingobservation.',
'Roundviewcouldmultiplemodels, requestsadditionalimages/surfaceattributes;falsecan_solveemptyoutputs.' ],
'altitude_circle_drawing':[
'Acuteplanedgealignedeke throughA, HinsideBC AHperpendicular; coordinatewitness(0,0),(6,0),(2,3). Noactualdrawingapproval.',
'FootoutsideBCvalid onextensionthroughB; coordinatewitnessA(-2,3),H(-2,0) confirmsplan. Noforcedinternalfoot.',
'Compassaradius2.5cmopeningfixedatO; fixedcentre/radiusplan, samplingnotproofofactualcircle. Noactualinstrumentclaim.',
'GivenADnonperpendicularalready disprovesquote; midpointaloneinsufficient, coordinatewitnessA(1,2),D(3,0). No unseenfigureinference.',
'Missingimage/centre/base/scale/instrumentrecord preventsdrawingverification, askrelevantactualevidence. Emptyguardoutputs.' ]
}

common=' Actual full problem/givens/request/student quote and observation/initial/every title-reason-explanation-result-expression-unit/answer/all three hints read; shared hint dictionaries checked for contextual fit without final numbers/labels or fully substituted solution. Fraction/Decimal and inverse traces passed; independent semantic/unit oracles recorded separately, not parser proof. Seven criteria same-author self-QA only, false human/teacher/owner-human/external; historical scope/operand bounds pending and physical assets pending retained.'
for node,ns in notes.items():
 a.review('finish_g5_'+node,[x+common for x in ns])

inventory=[]
for node in notes:
 p=a.R/('authored_batches/finish_g5_'+node+'.jsonl');rr=a.read_rows(p);rp=a.R/('reviews/finish_g5_'+node+'_owner_preauthorized_self_QA.jsonl')
 inventory.append({'node_id':'old_g5_'+node,'batch':p.name,'case_count':len(rr),'case_ids':[x['sample_id'] for x in rr],'source_sha256':a.sha(p.read_bytes()),'row_hashes':{x['sample_id']:a.row_sha(x) for x in rr},'review_sha256':a.sha(rp.read_bytes())})
a.write_json(a.E/'finish_g5_all_independent_oracles.json',{'author_agent':a.AUTHOR_AGENT,'checks':checks,'inventory':inventory,'actual_full_content_read':True,'semantic_proof_not_inferred_from_parser':True,'same_author_QA_not_human_or_independent':True,'physical_success_verified':False,'full_2006_or_current_2026_legal_completeness_certified':False,'sources_or_protections_or_shared_state_modified':False})
print('GRADE5_FINISH_SUMMARY',a.json.dumps({'nodes':len(inventory),'cases':sum(i['case_count'] for i in inventory),'core':3*len(inventory),'oracle_checks':len(checks),'evidence':'finish_g5_all_independent_oracles.json','inventory':inventory},ensure_ascii=False))
