"""Publisher TOC catalog and honest page-access boundaries; no textbook copying."""
from pathlib import Path
import json,hashlib
from build_sgk_g5_gap import RUN,OLD,SOURCE,dump,sha,V,save

TOC1='''1|6|Ôn tập số tự nhiên|natural
2|9|Ôn tập các phép tính với số tự nhiên|natural
3|11|Ôn tập phân số|fraction
4|14|Phân số thập phân|decimal_fraction
5|16|Ôn tập các phép tính với phân số|fraction
6|20|Cộng, trừ hai phân số khác mẫu số|fraction
7|23|Hỗn số|mixed
8|26|Ôn tập hình học và đo lường|geometry
9|29|Luyện tập chung|mixed
10|32|Khái niệm số thập phân|decimal_read
11|38|So sánh các số thập phân|decimal_read
12|42|Viết số đo đại lượng dưới dạng số thập phân|decimal_measure
13|47|Làm tròn số thập phân|round
14|51|Luyện tập chung|decimal_read
15|53|Ki-lô-mét vuông. Héc-ta|area
16|56|Các đơn vị đo diện tích|area
17|60|Thực hành và trải nghiệm với một số đơn vị đo đại lượng|measurement
18|62|Luyện tập chung|area
19|65|Phép cộng số thập phân|decimal_operation
20|68|Phép trừ số thập phân|decimal_operation
21|71|Phép nhân số thập phân|decimal_operation
22|76|Phép chia số thập phân|decimal_operation
23|83|Nhân, chia số thập phân với 10; 100; 1000;… hoặc 0,1; 0,01; 0,001;…|decimal_scale
24|88|Luyện tập chung|decimal_operation
25|91|Hình tam giác. Diện tích hình tam giác|triangle
26|98|Hình thang. Diện tích hình thang|trapezoid
27|105|Đường tròn. Chu vi và diện tích hình tròn|circle
28|113|Thực hành và trải nghiệm đo, vẽ, lắp ghép, tạo hình|drawing
29|116|Luyện tập chung|geometry
30|120|Ôn tập số thập phân|decimal_read
31|123|Ôn tập các phép tính với số thập phân|decimal_operation
32|127|Ôn tập một số hình phẳng|geometry
33|130|Ôn tập diện tích, chu vi một số hình phẳng|geometry
34|133|Ôn tập đo lường|measurement
35|135|Ôn tập chung|natural'''
TOC2='''36|4|Tỉ số. Tỉ số phần trăm|percent
37|8|Tỉ lệ bản đồ và ứng dụng|map
38|12|Tìm hai số khi biết tổng và tỉ số của hai số đó|ratio
39|15|Tìm hai số khi biết hiệu và tỉ số của hai số đó|ratio
40|18|Tìm tỉ số phần trăm của hai số|percent
41|21|Tìm giá trị phần trăm của một số|percent
42|23|Máy tính cầm tay|calculator
43|27|Thực hành và trải nghiệm sử dụng máy tính cầm tay|calculator
44|28|Luyện tập chung|percent
45|30|Thể tích của một hình|volume
46|33|Xăng-ti-mét khối. Đề-xi-mét khối|volume
47|35|Mét khối|volume
48|38|Luyện tập chung|volume
49|40|Hình khai triển của hình lập phương, hình hộp chữ nhật và hình trụ|net
50|44|Diện tích xung quanh và diện tích toàn phần của hình hộp chữ nhật|surface
51|48|Diện tích xung quanh và diện tích toàn phần của hình lập phương|surface
52|51|Thể tích của hình hộp chữ nhật|volume
53|54|Thể tích của hình lập phương|volume
54|58|Thực hành tính toán và ước lượng thể tích một số hình khối|volume
55|60|Luyện tập chung|volume
56|64|Các đơn vị đo thời gian|time
57|67|Cộng, trừ số đo thời gian|time
58|71|Nhân, chia số đo thời gian với một số|time
59|76|Vận tốc của một chuyển động đều|speed
60|78|Quãng đường, thời gian của một chuyển động đều|speed
61|82|Thực hành tính toán và ước lượng về vận tốc, quãng đường, thời gian trong chuyển động đều|speed
62|84|Luyện tập chung|speed
63|87|Thu thập, phân loại, sắp xếp các số liệu|data
64|90|Biểu đồ hình quạt tròn|pie
65|94|Tỉ số của số lần lặp lại một sự kiện so với tổng số lần thực hiện|trial
66|96|Thực hành và trải nghiệm thu thập, phân tích, biểu diễn các số liệu thống kê|data
67|100|Luyện tập chung|pie
68|103|Ôn tập số tự nhiên, phân số, số thập phân|natural
69|107|Ôn tập các phép tính với số tự nhiên, phân số, số thập phân|fraction
70|111|Ôn tập tỉ số, tỉ số phần trăm|percent
71|113|Ôn tập hình học|geometry
72|119|Ôn tập đo lường|measurement
73|121|Ôn tập toán chuyển động đều|speed
74|123|Ôn tập một số yếu tố thống kê và xác suất|trial
75|128|Ôn tập chung|natural'''
KEYS={'natural':['natural','multi_step','multistep'],'fraction':['fraction_operation','fraction_share','unlike'], 'decimal_fraction':['decimal_fraction'], 'mixed':['mixed'], 'geometry':['triangle','trapezoid','circle','shape'], 'decimal_read':['decimal_read','decimal_compare','decimal_pattern'], 'decimal_measure':['decimal_measure','mixed_units'], 'round':['round'], 'area':['area_km','mm2','area_land'], 'measurement':['measure','volume','area'], 'decimal_operation':['decimal_operation','decimal_divisor','decimal_multiply','decimal_product'], 'decimal_scale':['scale_10','multiplier','decimal_scale'],'triangle':['triangle','altitude'],'trapezoid':['trapezoid','trapezium'],'circle':['circle'],'drawing':['drawing','compass','net'], 'percent':['percent'], 'map':['map_','scale_map'], 'ratio':['ratio_sum','ratio_difference','sum_ratio','difference_ratio','ratio_total'], 'calculator':['calculator'], 'volume':['volume','m3_','tank'], 'net':['solid_nets','net_'], 'surface':['surface','cuboid','cube'], 'time':['time_arithmetic','time_'], 'speed':['speed','motion','moving','velocity'], 'data':['data','categor','survey','statistics'], 'pie':['pie'], 'trial':['trial','experimental','outcome']}
CONTENT={1:[14,23,47,83,105,110],2:[23,30,40,94,96,97,100]}

def build():
 lessons=[]
 for vol,txt,last in [(1,TOC1,138),(2,TOC2,134)]:
  parsed=[l.split('|') for l in txt.splitlines()]
  urls=json.loads((RUN/f'g5_sources/v{vol}_page_urls.json').read_text('utf-8-sig'))
  for i,(num,page,title,fam) in enumerate(parsed):
   start=int(page);end=int(parsed[i+1][1])-1 if i+1<len(parsed) else last
   candidates=[r for r in OLD if r.get('grade')==5 and any(k in (r.get('sample_id','')+' '+r.get('topic','')).lower() for k in KEYS[fam])]
   sampled=[p for p in CONTENT[vol] if start<=p<=end]
   lessons.append({'lesson_number':int(num),'volume':vol,'title':title,'printed_start_page':start,'printed_end_page_bound':end,'skill_family_catalog':fam,'official_viewer_url':V[vol],'official_start_page_image_url':urls[start+1],'toc_evidence':{'status':'ACTUALLY_READ_TOC','local_image_names':['v1_image_6.png','v1_image_7.png'] if vol==1 else ['v2_image_4.png','v2_image_5.png']},'content_pages_actually_read':sampled,'access_status':'TARGETED_CONTENT_SAMPLE_READ' if sampled else 'TOC_READ_CONTENT_PENDING','existing_mapping_status':'BROAD_FAMILY_CONTENT_PRESENT_REPRESENTATION_COMPLETENESS_NOT_CERTIFIED' if candidates else 'PENDING_MATCH_REVIEW','existing_matching_case_count':len(candidates),'existing_source_examples':[{'sample_id':r['sample_id'],'source_row_sha256':sha(dump(r).encode()),'topic':r.get('topic'),'problem':r.get('problem')} for r in candidates[:3]],'not_claimed':['every exercise viewed','all lesson subskills saturated','entire SGK or curriculum legally certified']})
 assert len(lessons)==75 and {x['lesson_number'] for x in lessons}==set(range(1,76))
 manifest=[]
 for p in sorted((RUN/'g5_sources').iterdir()):
  if p.is_file() and p.suffix in ['.png','.html','.pdf']:
   manifest.append({'filename':p.name,'bytes':p.stat().st_size,'sha256':sha(p.read_bytes()),'publication_policy':'REFERENCE_HASH_ONLY_NO_SGK_PAGE_BYTES_IN_DATASET'})
 updates={'v1_information':{'id':'1xtc24nyFelwPQwpnacp7nEicSQGbwsJl','read_method':'GOOGLE_DRIVE_CONNECTOR_EXTRACT_ACTUALLY_READ','changed_math_scope':'No operation-role change observed in this update information; place-name and real-world area facts updated.','notes':[{'page':38,'summary':'Administrative place labels updated for bridge references.'},{'page':55,'summary':'Huế city name and area fact updated; avoid reusing old factual area as current truth.'},{'page':58,'summary':'Map administrative boundaries updated.'}]},'v2_information':{'id':'1D4jWqIYASRfW5PHMGG10yIPawJX1tKHZ','read_method':'GOOGLE_DRIVE_CONNECTOR_EXTRACT_ACTUALLY_READ','notes':[{'page':10,'summary':'Route wording clarifies railway-station endpoints.'},{'page':17,'summary':'Punctuation adjustment.'},{'page':22,'summary':'Statement punctuation adjustment.'},{'page':100,'summary':'Known-part/find-whole problem changed to known-whole/find-part. Both relational roles included as original paired examples.'},{'page':124,'summary':'Regional chart after administrative updates.'},{'page':125,'summary':'Regional chart/data-label updates.'}]},'v2_updated_pages':{'id':'1XmfQ_xbZa0sOA9Sc4GsiC0MPiHLhnSNX','pages_actually_read_from_connector':[10,17,22,100,124,125]},'v1_updated_pages':{'id':'1tDhNWWQcG0_J7tpW-PlKfXu-F4yYNxhe','status':'RAW_RETRIEVED_BY_ROOT; CONTENT_NOT_CLAIMED_READ_BY_THIS_AUTHOR'},'raw_hash_receipt':'g5_sources/official_update_raw_hashes.json'}
 save('sgk_g5_catalog.json',{'version':'sgk_kntt_g5_targeted_catalog.v1','grade':5,'edition_evidence':'Public publisher viewer images retrieved October 2026; title says second reprint; vol1 colophon identifies 2026. Updates separately checked.','official_book_viewers':V,'lessons':lessons,'totals':{'toc_lessons_read':75,'volume1_lessons':35,'volume2_lessons':40,'public_page_images_indexed':282,'targeted_book_content_pages_read':CONTENT,'all_book_pages_read':False},'comparison':{'actual_rows':len(OLD),'source_file':str(SOURCE),'source_sha256':sha(SOURCE.read_bytes()),'managed_corpus_total_from_parent':1629386,'bulk_domain_note':'Pure arithmetic domains checked by parent cloud state/ranges, not treated as missing because absent from selected view. All 5,683 nonbulk and small Fraction/Decimal source records restored.'},'updates_2026':updates,'access_manifest':manifest,'limits':['TOC supplies lesson bounds, not exercise completeness.','Broad family mappings are actual existing case references; they do not prove every SGK subskill is covered.','No wholesale exercise text or textbook image bytes in produced data.','New original representation enrichment is finite and does not increase original core quota.']})
 print('catalog',len(lessons),'unmatched',sum(not l['existing_matching_case_count'] for l in lessons))
if __name__=='__main__':build()
