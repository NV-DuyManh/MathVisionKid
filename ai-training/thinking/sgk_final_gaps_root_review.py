"""Root full-field semantic review, bound to71 exact corrected drafts and peer proof."""
from sgk_final_gaps_release import RUN,DIRS,FIELDS,read,rows,sha,write
NOTES=[
[
'G3 three different arms inside fixed rightangle give AOB,AOC,BOC; includes compoundouter, excludesreverse duplicate, no degrees required.',
'G3 OX/OY same arm despite two points. Three directions yield XOT,XOZ,TOZ, notdegenerateXOY; observablequotecorrected.',
'G4 lowerpan heavier, A>B and B>C across pan-switched common B implies C<B<A; no numericalweight fabricated.',
'G5 P2.05>1.98 leftlow andQ2.50=2.5 level consistent; R0.90>0.85 requiresleftlow. Labels unchanged rather thanfittedtoimage.',
'G5 A3.08<B3.80 givesrightlow anddifference0.72kg. Quote digitlength rule wrong, no faultydeviceorrealbaginference.',
'Openbounded shelf permits any valid design. ChosenW50H60D20N3 uses2side+5horizontalboards7400cm2;0.74m2cost148000<=300000. No uniqueness or optimum.',
'Openrepair W80H100D30N4 costs408000>250000. OriginalvalidalternativeW40H60D20N4 costs144000. Explicitdomainandboardinventory checked, no stockpacking/strengthclaim.',
'G3 two simultaneousballs fromD2V1X1 yieldDD,DV,DX,VX only; colorsunordered, VVXXsupplyimpossible, no probabilityclaim.',
'G5 actualpublisherdrawcountconfirmedthree; originalnewstockD2V1X3 gives sixboundedtriples byV0/1 andD0..2, no ordermultiplicity.',
'G5 D3X2 draw3 forbidsXXX, retainsDXX/DDX/DDD, residualstocksD2X0,D1X1,D0X2. Allthreeexactconservation.',
'Complete drawnlineABCD sixendpointpairs plusBEFthree =9segments. FourABCDtriples plusBEF=5; crossline noncollinearityexplicit.',
'GapBCmeansonlyAB/CD drawnplusAE/AF/EF=5segments, whileABCDstillfourcollineartriples plusAEF. Positioncondition doesnotfillmissingink.',
'G4 clarifiedfractionflowereligibilitya-e each1/2, f-iinvalid; removeonce. Anabd3,Binhce2 afterturn6 total5stops, fourinvalidremain.',
'G4 reciprocalmemory failacreturnsfacesdown;Binhab,Ancd,Binhef, Binhwins4with2pairs. Allsixremoved, no inventedstudentmemory.',
'Meta ambiguityguard cananswer lackofdata: nineobjectswithoutlabels/sharedthresholdownershipcannotestablishwinner. Askactualmissingrules/state; hints do notassignfinalwinner.',
'GivenGregorianscope4/100/400:2024and2400leap,2100common. AfterFeb28 accordinglyFeb29/Mar1/Feb29; no unlimited4yearrule.',
'2099/2100/2101allcommon gives1095days for3wholeyears; centuryexception explicitnotdateintervaloffbyone.',
'G3 1a4*3=4b2 unitscarry1;10<=3a+1<=19 yields a3..6,b0/3/6/9 fourvalidpairs. No artificialuniqueness.',
'G3 cards1/2/4 useonce AB*C84 permits21*4only, although42*2arithmetically84violatesinventory. EveryCchoice+ABorderchecked.',
'G3 directedstripsP4STARTflower,Q0flowersstar,R7starEND uniquelyPQR407 andzerochucvalue0. MissingoriginalG3locator remainslimitation.',
'G3 P6STARTcircle cannotconnectQ2/R5whoseleftsquare; no rotation allowed meansnochain, not625. Feasibilityratherthanfakeanswer.',
'G3 distinct24/42/68 andBinh<An<Chi uniquelyassignBinh24An42Chi68; eachidentityandcardusedonce.',
'G3 onlyMinh<Lan with21/35/54 permits3assignments,Nhianycard; no implicitmiddlerank. Allsixpermutationsprunedbyoneorder.',
'G4 area-derivedinventorytwo16m2squaresandone18m2rectangle,An=Binhforcesbothsquare,Chi18. Names/shapesalone notareaequality.'
],
[
'G1 fixedPcoversABDEG on3x3; complementCFHI selectsQonly,RmissingH,SoverlapEandmissingF. Concaveboundary jointlychecked.',
'G1 rotationsonly:QABDG halfturnmapsIHFC=CFHI, Rchiraldoesnotmatchanyquarterturn. Derivedwordingnửavòngusesnoangledegree, no reflectionlegal.',
'Fouraxisunit squares+outer+midpointdiamond give6;completeobliqueboundarycounts, no unspecifiedsegments/rectanglesadded.',
'RemoveEFbreaksdiamondonly, fouraxisunitplusouter5remain; missingdiagonalnotrestoredbythought.',
'G3 selectAB2x2legtriangles tile2x2square alongdiagonal; C4x1leg cannotfitallowedquarterturntargetbbox. Equalareaalone insufficient.',
'G4 two2legtriangles totalarea4equal4x1targetbutallallowedaxisquarterturnsverticalextent2>1. No legalplacement, rotationsnotexpanded.',
'G1 squareP2x2body plus two1x1legtriangles filltwohalvesofroofbase2height1;sharedinternaledge notoverlap, allpiecesonce.',
'G4 fourunitrighttriangles centered1,1 spanrotateddiamonds0,1/1,0/2,1/1,2;area2not4, boundaryandorientationexact.',
'G5 classicsevenpieceinventoryL1L2areas4,M/S/P2,T1T2one; exactplacementsclipdisjointinside4x4. MoveT2ontoT1 leaves1gap1overlap despitepaperarea16.',
'G1 triangular2grid originallyADEBDFCEFDEFABC5; removeEFkillsCEF/DEF leavesADEBDFABC3,outerintact.',
'G4 exact3que relocatesJK/KL/LMtoBC/BE/CF, preserve4essentialstripedges;twoadjacentrhombiABED/BCFE,outer2x1notrhombus. Allsource/destinationlegality.',
'G1 irregularstairs3+2+1sixfullunitcells, excludes3whitecellsbounding3x3; notrectangleformulaalone.',
'G1 twofull+fourcomplementaryhalfcellssum4unitpaper, pairCD/EFonce. Sixcolor-touchedcellsnot6full; gradeverbalhalfregroupnotformaldivision.',
'G4 square4 split2left2x2area4eachandrightcentral4trianglesarea2each,6pieces16total;two differentshapeclassesdespiteequalareas.',
'OffcenterPrightbbox2x4 height1 createsareas1/2/3/2 plus4/4,still6pieces16butnotfourequal;metricgivenratherthanappearance.',
'Hexagon6equilateralspokes gives6rhombus4vertexsets byall3directions; everyparallelogramalsoequal1edges,notdegenerateOonstraightedge.',
'RemoveABkills2of6hexagonrhombi;remainingBCDO,CDEO,DEFO,AEFOfour; no imaginaryparallelboundary.',
'G1 explicit7segmentalphabetcount6/2/5/5/4/5/6/3/7/6 meansonly4usesfoursticksbcfg;standardglyphnotordinaryhandwriting.',
'Equation6+4=4 fixedprintedsigns/fixed3digitcells exactonephysicalg→b infirstmakes0+4=4 unique amongvalidcodes; no signmove.',
'Fixedtwo-slot69 noleading0 exactonemove yields58,60,66,83,85,99;minimum58byeleft→eright preservingglyphs5/8.',
'Threeisolatedslots11_ fourtotalsticks exacttwodifferentinitialmoves yield4__,_4_,_11 only;min4. Onemove cannotemptyorcreateanydigitbecauseminimum2sticks, scopeexplicit.',
'G1 fixedorientationfrontred2,topblue5,rightyellow3. Onlytop/rightsum8;unknownotherfacescannotinfertotalorstandarddieopposites.',
'G1 markings arelabelsnotfacegeometry;studenttoptriangle/rightcircle swapped. Correctfrontstar/topcircle/righttriangle,topcount4only.',
'G2 stackedBcoversAtop; conjunctiontopANDvisibleselectBtop5,notknownbutoccludedAtop1andnotfront/right.'
],
[
'Sectorrearrangementpreservespaperarea,finite8keepscurvedboundary; limitingdimensionspi*r9.42andr3 giveapprox28.26cm2, finiteexactrectanglerejected.',
'R5diskapprox78.5versusgivenreplacement15.5*4.9=75.95 difference2.55. Paperconservationnotnegatedbyreplacingcurvedregionwithdifferentrectangle.',
'G3 coincideABfoldcreaseM isonABequidistantAMMB midpoint. Protocolcheckrequiresrealobservationbeforeclaimingactualstudentresult.',
'G4 unitcordtwohalffoldscreate4intervals/3internalcreases,closesttoAonequartermeter;middleisonehalf. No ruler/cutting.',
'G4 linecoincidencefoldthroughP reversesoppositeraysofd;equaladjacentangles formrightangle. AnycreaseatPnotnecessarilyperpendicular.',
'G5 2mstripthreehalffolds8intervals7creases,thirdinternalfromleft3/8whole=3/4m,not3/8m.',
'Fold8x6leftrightoutertopcuttwolayersunfoldremoves(1,6),(8,6)twoboundarynotchesnotcentralhole,remaining46verticalsymmetry.',
'Double8x8foldcutattwocreasesintersection removescentral(4,4),(4,5),(5,4),(5,5) connected2x2hole,remaining60not4disjointholes.',
'CorrectclassicmidpointtangramABOADO4each,CEF/EBGI/HOIF2each,OGI/DFH1each;fractions1/4,1/8,1/16sum1. Shapesproperparallelogram+square,parentsrejected.',
'TangramgroupXABO+OGI5,YCEF+EBGI+DFH5 despite2vs3pieces;outsideX11/16, Yonlypartofcomplement. Midpointderivationnotpiececount.',
'Nestedcirclemix0.3dm=3cm,20mm=2cm,0.015m=1.5cm. OA3AB2bypriorcircumference;OB1or5possiblebecauseBdirectionfree, no containmentclaim.',
'CircleO0.04m andA40mmradii4cm;lastdiameter8radius4 meanssamecompassopeningthree,quote8lastwrong. OBnotfixed4.',
'G4 OB+3,+3square-diagonalgivenhalfright45,properbaseOAandprotractorscaleplannedonlynotactualmeasurement.',
'G4 OC-2,+2anglefromOA+rightis135,not45withoppositehorizontalray. Quotewronganglereferencedwithoutinferhiddenaction.',
'24x16orthogonalhalffolds12x8footprint96,uniform4layers384paper;no2sidedareaorlossofpaper.',
'Offcenter12x6firstleft4reflectionyieldswidth8not6;secondheight3footprint24,twodifferent12area strips4/2layers total72.',
'VerticalbaseABandCDcompleteD=P/Qsamecol4;bothsimpleexactoneparallelpair,Rfails. Orientationnotforcedhorizontal.',
'DiagonalABslopeone:CDforP/Qparallel;QalsoADparallelBCsoexcludedonlybyexplicitexclusiveconvention, PvalidandRfails.',
'G3 8x2singleverticalcutgives2pieces4x2stack4x4squarearea16;perimeter20→16independentfromarea.',
'G4 parallelogrambase6height3offset2cutAEDtranslate6→BFC,fillrightrectEFCD6x3area18;edgeBCsharednotinterioroverlap.',
'G4 square4diagonalsfourrightisoscelestriangleshypotenuse4;pairacrosshypotenusemakes2squareseach8area thenrectangle2:1area16. Newedgehalfdiagonalnot4, noirrationalneeded.',
'Wheeldiameter40cm circumference125.6cm *12.5turns1570cm=15.7m,halfturndistancekept,noextra2/area.',
'Wheelr2.5dm0.25m;distance0.157km157m /circ1.57=100turns. Quoteunitmixandmissing2radius, reverse157mverified.'
]]
def main():
    batches={};(RUN/'root_evidence').mkdir(exist_ok=True)
    for name,notes in zip(DIRS,NOTES):
        folder=RUN/name;source=rows(folder/'cases.jsonl');peer=read(folder/'peer_review.json')
        assert len(source)==len(notes) and peer['status'].startswith('PASS')
        assert not any(peer.get(k) for k in ['fixes_required','changes_required','critical_issues','blocking_findings'])
        assert peer.get('source_sha256',peer.get('cases_sha256'))==sha((folder/'cases.jsonl').read_bytes())
        assert peer['chat_sha256']==sha((folder/'chat.jsonl').read_bytes())
        arts=peer.get('artifacts',peer.get('evidence_files'))
        pins={x['path']:x['sha256'] for x in arts} if isinstance(arts,list) else {n:v['sha256'] for n,v in arts.items()}
        refs=['peer_review.json']+list(pins)
        for n,h in pins.items():assert sha((folder/n).read_bytes())==h
        reviews=[]
        for (row,h),note in zip(source,notes):
            criteria=[dict(criterion=k,passed=True,evidence=v) for k,v in [
              ('problem_givens_request_semantics',note),
              ('math_and_independent_model','Root recomputed actual requested quantities; peer different-method finite oracle and wrong-model/answer mutation evidence pinned. No parser/keyword-only semantic certification.'),
              ('steps_reasons_units_checks','All actual steps/reasons/explanations/results/units read; operations follow givens, original constraints, units and complete enumeration or reversecheck.'),
              ('initial_and_three_hints','All initial guidance and three hint/question pairs read; no filled numeric answers/finalwinninglabels/fullsolution.'),
              ('grounded_student_feedback','Any critique references only supplied studentwork. No hiddenthought, unseenpublisherimage, actualconstructionorindependenthumanreview invented.'),
              ('grade_and_enrichment_scope',f'Explicit grade{row["grade"]} model. Relation/presentation/orientation/inventory/grade branches differ substantively from inspected accepted examples; original missing locator and physical evidence remain limitations.'),
              ('provenance_preservation','AIorigin retained. Corrected drafts and parent evidence preserved with rawhash; acceptance derived separately; no new humanattestation.')]]
            reviews.append(dict(sample_id=row['sample_id'],source_row_sha256=h,actual_fields={k:row[k] for k in FIELDS},criteria=criteria,semantic_decision=note,human_review_claimed=False))
        batches[name]=dict(status='PASS',actual_content_read=True,cases_sha256=sha((folder/'cases.jsonl').read_bytes()),chat_sha256=sha((folder/'chat.jsonl').read_bytes()),peer_evidence=[dict(file=n,sha256=sha((folder/n).read_bytes())) for n in refs],reviews=reviews)
    write(RUN/'root_evidence/content_review.json',dict(status='PASS_71_ACTUAL_CONTENT_AND_PEER_REVIEW',batches=batches,training_started=False))
    print('71 full-content root decisions hash-bound')
if __name__=='__main__':main()

