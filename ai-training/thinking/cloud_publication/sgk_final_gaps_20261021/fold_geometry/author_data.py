"""Original finite text models. No training or physical-execution claim."""
def author(put,st,W):
 m=W[0]
 put(m,'sector_limit_not_exact_rectangle',5,
 'Đĩa giấy tròn bán kính 3 cm chia thành số chẵn miếng quạt bằng nhau, xếp xen kẽ đầu nhọn lên và xuống, không chồng hay bỏ giấy. Với 8 miếng, hai mép dài vẫn cong. Khi chia ngày càng nhiều miếng bằng nhau, hình xếp tiến gần hình chữ nhật có chiều rộng là bán kính và chiều dài là nửa độ dài đường tròn. Dùng 3,14 tính gần đúng. Giải thích diện tích đĩa từ cách xếp và nhận xét câu “Ngay 8 miếng đã là hình chữ nhật chính xác”.',
 'Giải thích công thức, diện tích gần đúng và giới hạn của hình xếp hữu hạn',[
 st('Giữ đúng miền giấy','Cắt và chuyển đủ mảnh không làm mất hay chồng diện tích.','Diện tích giấy không đổi','Bảo toàn diện tích không biến các cung cong hữu hạn thành đoạn thẳng.'),
 st('Nhận hai kích thước tiến gần','Các cung chia đều lên hai mép; mỗi mép mang nửa chu vi.','9.42','Nửa chu vi gần đúng là 3,14 × 3 = 9,42 cm; chiều rộng tiến gần 3 cm. Các nếp nhấp nhô giảm khi miếng nhỏ hơn.','314/100*3','cm'),
 st('Suy diện tích rồi kiểm lời nói','Tích hai kích thước của hình chữ nhật tiến gần là nửa chu vi nhân bán kính.','28.26','9,42 × 3 = 28,26 cm² gần đúng. Công thức là 3,14 × bán kính × bán kính theo quy ước. Câu 8 miếng chính xác sai vì mép vẫn cong.','942/100*3','cm²')],
 [('Diện tích gần đúng','28.26','cm²'),('Câu 8 miếng','Sai, mép vẫn cong','')],
 dict(kind='disk',radius='3',pi='3.14',area='28.26',finite_exact=False),
 'Finite curved sector arrangement versus limiting rectangle; not formula-only.')
 put(m,'sector_rectangle_substitution_error',5,
 'Đĩa giấy bán kính 5 cm chia 16 miếng quạt bằng nhau rồi xếp xen kẽ không hao hụt. Mép vẫn cong. Bạn dùng hình chữ nhật dài 15,5 cm, rộng 4,9 cm để ước lượng hình xếp. Dùng 3,14 tính gần đúng diện tích đĩa; tính diện tích hình chữ nhật thay thế và chênh lệch. Giải thích vì sao hai số khác không phủ nhận bảo toàn giấy.',
 'Hai diện tích, độ lệch và nguyên nhân',[
 st('Giữ vật được tính','Đĩa thật dùng bán kính; hình chữ nhật thay thế có kích thước riêng.','78.5','3,14 × 5 × 5 = 78,5 cm² là giá trị gần đúng theo quy ước.','314/100*5*5','cm²'),
 st('Tính hình thay thế','Các kích thước được cho chưa phải kích thước giới hạn chính xác.','75.95','15,5 × 4,9 = 75,95 cm²; đây là mô hình chữ nhật thay miền cong.','155/10*49/10','cm²'),
 st('Kiểm bước ước lượng','Cắt xếp giữ giấy, thay đường biên cong bằng chữ nhật là một bước khác.','2.55','78,5 − 75,95 = 2,55 cm². Không dùng diện tích hình thay thế để nói 16 miếng đã thành chữ nhật chính xác.','785/10-7595/100','cm²')],
 [('Đĩa gần đúng','78.5','cm²'),('Chữ nhật','75.95','cm²'),('Lệch','2.55','cm²')],
 dict(kind='disk_estimate',radius='5',pi='3.14',rectangle=['15.5','4.9'],area='78.5',rect='75.95',gap='2.55'),
 'Finite substitution approximation error distinct from conservation.')
 m=W[1]
 put(m,'g3_coincidence_midpoint',3,
 'Dải giấy thẳng AB chưa chia vạch. Không dùng thước đo. Được gấp để đầu A trùng đầu B, miết một nếp rồi mở. Nếp cắt đoạn AB tại M. Giải thích M chia AB như thế nào và cách kiểm bằng gấp lại. Chưa có ảnh giấy của học sinh.',
 'Quan hệ hai đoạn và cách kiểm',[
 st('Đặt đúng hai đầu','Hai đầu cần trùng và dải không lệch.','A trùng B','Miết nếp sau khi hai đầu trùng; đây là kế hoạch, chưa chứng nhận thao tác thật.'),
 st('Dùng trùng khít','Hai phần của dải đối xứng qua nếp.','AM = MB; M là trung điểm AB','Gấp lại thì đoạn từ M đến A phủ khít đoạn từ M đến B nên chúng bằng nhau.'),
 st('Kiểm hai điều kiện','Trung điểm nằm trên đoạn và cách đều hai đầu.','M nằm trên AB và AM = MB','Muốn nhận xét dải thật, cần quan sát nếp và sự trùng hai đầu, không đoán từ mô tả.')],
 [('Quan hệ','AM = MB',''),('Vị trí','M là trung điểm AB','')],dict(kind='fold_equal',parts=2,selected=1,total=None),
 'G3 midpoint by endpoint coincidence, no ruler or observed-result claim.')
 put(m,'g4_cord_quarter_without_ruler',4,
 'Sợi dây thẳng dài đúng 1 m, hai đầu A,B. Không dùng thước đo hay cắt. Gập hai đầu trùng nhau; giữ dây gập rồi lại đặt hai đầu của đoạn gập trùng nhau, sau đó mở hết. Giả sử dây không giãn, nếp đúng. Hãy chọn từ A tới nếp đầu tiên để lấy một phần tư mét, nêu cách nhận nếp và vì sao không chọn nếp giữa.',
 'Nếp cần lấy, độ dài và kiểm',[
 st('Gập lần đầu','Hai đầu trùng chia chiều dài thành hai phần bằng nhau.','Hai nửa bằng nhau','Nếp giữa sau một lần mới là nửa dây.'),
 st('Chia đôi đoạn gập','Gấp đôi nữa chia mỗi nửa thành hai phần bằng nhau.','Mở ra có bốn khoảng bằng nhau','Có ba nếp trong; chọn nếp gần A nhất, không chọn nếp giữa.'),
 st('Kiểm theo đơn vị toàn dây','Bốn khoảng bằng nhau ghép đủ 1 m.','1/4','Đoạn từ A tới nếp gần nhất là một phần trong bốn phần bằng nhau, tức 1/4 m; bốn đoạn ghép lại đúng toàn dây.','1/4','m')],
 [('Độ dài chọn','1/4','m'),('Nếp','Nếp trong gần A nhất','')],dict(kind='fold_equal',parts=4,selected=1,total='1'),
 'G4 unit cord subdivision, not measuring or supplying a numerical mark.')
 put(m,'g4_perpendicular_coincidence_fold',4,
 'Trên giấy có đường thẳng d và điểm P nằm trên d, còn đủ giấy hai phía. Không dùng ê ke hay thước đo góc. Hãy nêu cách gấp cho hai phần của chính d trùng nhau, giữ P đứng yên trên nếp, để tạo nếp qua P vuông góc d. Vì sao chỉ gấp một nếp bất kỳ qua P chưa đủ? Không có ảnh thực.',
 'Quy trình dựng, lý do và điều kiện kiểm',[
 st('Buộc đúng điểm và đường','Nếp qua P, hai phần d ở hai phía P cần phủ nhau.','Giữ P trên nếp, chỉnh d trùng chính nó','Gấp một phía sang phía kia, giữ P trên nếp rồi miết khi hai nửa đường thẳng phủ nhau.'),
 st('Dùng hai góc bằng nhau','Hai phần d trùng làm hai góc giữa nếp với d bằng nhau.','Nếp vuông góc d','Hai góc bằng nhau ghép thành góc bẹt, nên mỗi góc là góc vuông.'),
 st('Kiểm đủ điều kiện','Qua P là một điều kiện, chưa buộc hai góc bằng nhau.','Kiểm qua P và hai phía d trùng','Nếp xiên qua P không làm hai phía d phủ nhau. Chưa quan sát nên không chứng nhận giấy học sinh đã gấp đúng.')],
 [('Kết quả mô hình','Nếp qua P vuông góc d','')],dict(kind='perpendicular_fold',angle='90',point_fixed=True,line_coincides=True),
 'G4 explicit perpendicular fold with equality of adjacent angles.')
 put(m,'g5_three_eighths_nonunit_strip',5,
 'Dải giấy dài đúng 2 m. Không dùng thước hay cắt. Gấp đôi dải, gấp đôi đoạn đang chồng, rồi gấp đôi lần nữa, mỗi lần đặt hai đầu của đoạn gập trùng nhau. Mở hết, giả sử không giãn và nếp đúng. Chọn từ đầu trái tới nếp trong thứ ba để lấy 3/8 chiều dài. Nêu độ dài và kiểm số khoảng.',
 'Độ dài đoạn chọn và cách đếm khoảng',[
 st('Theo dõi chia đôi','Mỗi lần gấp đôi tăng gấp đôi số khoảng bằng nhau.','Tám khoảng bằng nhau','Ba lần gấp tạo bảy nếp trong; nếp thứ ba cách đầu trái ba khoảng, không phải bốn.'),
 st('Giữ đơn vị toàn dải','Một phần tám phải lấy trên dải 2 m.','3/4','2 × 3/8 = 3/4 m; không lấy 3/8 m vì toàn dải không dài 1 m.','2*3/8','m'),
 st('Kiểm phần còn','Ba khoảng được lấy và năm khoảng còn ghép đủ tám.','Đúng 3/8 của dải trong mô hình','Kiểm sự trùng khít của các khoảng khi gấp, chưa khẳng định nếp thật chính xác.')],
 [('Độ dài','3/4','m')],dict(kind='fold_equal',parts=8,selected=3,total='2'),
 'G5 nonunit fraction by folding and explicit interval counting.')
 m=W[2]
 put(m,'fold_outer_edge_two_notches',4,
 'Giấy chữ nhật 8 cột,6 hàng ô vuông. Gấp mép trái trùng mép phải, nếp giữa cột 4 và 5. Phần chồng rộng 4 ô. Ở mép ngoài bên phải đang chồng, cắt bỏ qua cả hai lớp một ô ở góc trên rồi mở hết. Cột từ trái 1 đến 8, hàng từ dưới 1 đến 6. Theo mô hình cắt chính xác, liệt kê ô mất, số ô còn và trục đối xứng. Không có ảnh cần đo.',
 'Vết cắt sau mở, số ô và đối xứng',[
 st('Theo dõi mép đang trùng','Mép ngoài chồng gồm hai mép trái và phải ban đầu.','Hai vết cắt phản chiếu','Vết cắt không ở nếp giữa; mở giấy tạo hai khuyết ở góc trên trái, trên phải.'),
 st('Gắn hàng cột','Hai ô đối xứng cùng hàng và hai cột đối nhau.','Mất (1,6),(8,6)','Vết cắt chạm mép ngoài nên không thành lỗ ở giữa. Trục đối xứng là nếp giữa cột 4 và 5.'),
 st('Kiểm diện tích','Mỗi lớp bỏ một ô khác nhau.','46','8×6−2=46 ô còn, không chỉ trừ một vì lúc gập chỉ thấy một miếng chồng.','8*6-2','ô vuông')],
 [('Ô mất','(1,6),(8,6)',''),('Còn','46','ô vuông'),('Trục','Giữa cột 4 và 5','')],dict(kind='fold_cells',w=8,h=6,removed=[[1,6],[8,6]],expected=46,folds=['x=4']),
 'Single-fold reflected exterior notches, explicit original cells.')
 put(m,'double_fold_central_connected_hole',4,
 'Giấy vuông 8×8 ô. Gấp mép trái trùng phải theo giữa cột 4 và 5, rồi mép dưới trùng trên theo giữa hàng 4 và 5. Phần chồng có 4 lớp. Cắt bỏ đúng một ô ở góc mà hai nếp gấp gặp nhau, qua cả bốn lớp; mở hết. Hàng,cột ban đầu đều từ 1 đến 8. Liệt kê ô mất, chúng tạo một lỗ hay bốn lỗ rời, và số ô còn. Giả sử cắt đúng các cạnh ô.',
 'Phản chiếu qua hai nếp và biên lỗ',[
 st('Mở từng nếp','Mỗi lần mở đưa vết cắt sang phần đối xứng.','Bốn ô gặp tại tâm','Ô kề cả hai nếp đi tới bốn phía của tâm giấy, không tới bốn góc ngoài.'),
 st('Liệt kê và kiểm kề','Cột và hàng sát nếp đều là 4 hoặc 5.','Mất (4,4),(4,5),(5,4),(5,5)','Bốn ô chung cạnh ghép lỗ vuông 2×2 ô ở giữa; không phải bốn lỗ rời.'),
 st('Kiểm diện tích','Bốn lớp bỏ bốn ô khác nhau trên giấy mở.','60','8×8−4=60 ô còn. Lỗ đối xứng qua cả hai nếp gấp.','8*8-4','ô vuông')],
 [('Ô mất','(4,4),(4,5),(5,4),(5,5)',''),('Lỗ','Một lỗ vuông 2×2 ô ở giữa',''),('Còn','60','ô vuông')],dict(kind='fold_cells',w=8,h=8,removed=[[4,4],[4,5],[5,4],[5,5]],expected=60,folds=['x=4','y=4']),
 'Two-fold propagation and connected central cut boundary.')
 m=W[3]
 pieces=[[(0,0),(4,0),(2,2)],[(0,0),(0,4),(2,2)],[(4,4),(4,2),(2,4)],[(2,2),(3,1),(4,2),(3,3)],[(4,0),(4,2),(3,1)],[(0,4),(2,4),(1,3)],[(1,3),(2,2),(3,3),(2,4)]]
 base='Hình vuông ABCD cạnh 4 ô, A dưới trái,B dưới phải,C trên phải,D trên trái. O là tâm; E là giữa BC,F là giữa CD; G là giữa OB,H là giữa OD,I là giữa OC. Cắt đúng các biên để có bảy mảnh: ABO,ADO,CEF,OGEI,BEG,DFH,HOIF; tên đa giác ghi theo thứ tự quanh biên. Không bỏ giấy. Mỗi ô cạnh 1 cm. '
 put(m,'tangram_midpoint_seven_piece_inventory',5,base+'Tính diện tích và phần của cả hình của từng mảnh, kiểm tổng. Không có hình ẩn cần đo.',
 'Bảng diện tích bảy mảnh và phân số',[
 st('Theo điểm giữa','O chia đôi đường chéo, các điểm E,F,G,H,I là điểm giữa đã chỉ.','ABO,ADO mỗi mảnh 4 cm²','Đáy mỗi mảnh 4 cm và cao 2 cm nên diện tích 4 cm², bằng 1/4 cả hình 16 cm².','4*2/2','cm²'),
 st('Tính đủ các mảnh','Dùng đáy và cao theo ô; tách hình vuông và hình bình hành thành hai tam giác.','CEF,OGEI,HOIF mỗi mảnh 2 cm²; BEG,DFH mỗi mảnh 1 cm²','CEF có hai cạnh vuông góc 2 cm, diện tích 2. BEG,DFH có đáy 2 cao 1, diện tích 1. OGEI,HOIF mỗi hình tách thành hai tam giác diện tích 1; các phần lần lượt 1/8 và 1/16.'),
 st('Kiểm khép kín','Các mảnh cắt chỉ chung biên, không chung phần trong.','16','4+4+2+2+1+1+2=16 cm²; 1/4+1/4+1/8+1/8+1/16+1/16+1/8=1.','4+4+2+2+1+1+2','cm²')],
 [('ABO,ADO mỗi mảnh','1/4','hình'),('CEF,OGEI,HOIF mỗi mảnh','1/8','hình'),('BEG,DFH mỗi mảnh','1/16','hình')],dict(kind='tangram',pieces=pieces,square_side=4,areas=['4','4','2','2','1','1','2']),
 'Complete seven-piece tangram derived from square midpoint geometry.')
 put(m,'tangram_group_equal_area_different_count',5,base+'Nhóm X gồm ABO và BEG; nhóm Y gồm CEF,OGEI,DFH. So diện tích hai nhóm và tìm phần giấy ngoài X. Vì sao số mảnh không quyết định nhóm nào lớn hơn?',
 'So nhóm và phần bù',[
 st('Lấy diện tích theo hình học','Mảnh lớn và mảnh nhỏ không cùng diện tích.','5','ABO diện tích 4 cm², BEG 1 cm² nên X=5 cm²; không lấy số mảnh làm phân số trên bảy.','4+1','cm²'),
 st('Tính nhóm còn lại','Hai mảnh 2 cm² và một mảnh 1 cm².','5','Y=2+2+1=5 cm². Hai nhóm bằng nhau dù X hai mảnh,Y ba mảnh.','2+2+1','cm²'),
 st('Kiểm phần bù','Cả hình 16 cm² gồm X và phần ngoài X.','11/16','Ngoài X có 16−5=11 cm² tức 11/16 hình; Y chỉ là một phần của phần ngoài X, không phải toàn bộ.','(16-5)/16','hình')],
 [('So','X và Y bằng nhau, mỗi nhóm 5 cm²',''),('Ngoài X','11/16','hình')],dict(kind='tangram_groups',pieces=pieces,x=[0,4],y=[2,3,5],square_side=4,x_area='5',y_area='5',complement='11/16'),
 'Different-count equal-area grouping and complement using exact full dissection.')
 m=W[4]
 put(m,'mixed_unit_center_on_previous_circle',5,
 'Vẽ đường tròn tâm O bán kính 0,3 dm. Chọn A trên đó, vẽ đường tròn tâm A bán kính 20 mm. Chọn B trên đường tròn tâm A rồi vẽ đường tròn tâm B bán kính 0,015 m. Chỉ cần chuỗi thỏa điều kiện, không bắt các tâm thẳng hàng hay đường tròn nằm trọn trong nhau. Đổi độ mở compa về cm; chỉ ra OA,AB; có biết OB duy nhất không? Chưa có bản vẽ thật.',
 'Độ mở, khoảng tâm và điều chưa xác định',[
 st('Đổi bán kính','Compa mở theo bán kính của đường tròn đang vẽ.','3 cm;2 cm;1,5 cm','0,3 dm=3 cm;20 mm=2 cm;0,015 m=1,5 cm. Chuyển kim từ O tới A rồi tới B đúng thứ tự.','15/1000*100','cm'),
 st('Kiểm tâm sau','Điểm trên đường tròn cách tâm bằng bán kính của chính đường tròn đó.','OA=3 cm;AB=2 cm','Chọn A trên đường tròn O, B trên đường tròn A; bán kính cuối 1,5 cm không quyết định AB.'),
 st('Xét điều thiếu','Hướng chọn B quanh A chưa được ấn định.','OB không duy nhất','B trên tia OA phía xa O cho OB=5 cm; B trên đoạn AO cách A 2 cm cho OB=1 cm. Hai ví dụ đều thỏa, không đoán tất cả đường tròn lồng trọn nhau.')],
 [('Độ mở','3;2;1,5','cm'),('OA','3','cm'),('AB','2','cm'),('OB','Không duy nhất: ví dụ 1 cm hoặc 5 cm','')],dict(kind='circle_chain',radii=['0.3 dm','20 mm','0.015 m'],cm=['3','2','1.5'],ob_examples=['1','5']),
 'Mixed-unit compass chain with dependent centers and explicit nonuniqueness.')
 put(m,'same_compass_opening_radius_diameter',5,
 'Đường tròn O bán kính 0,04 m. Chọn A trên đó, vẽ đường tròn A bán kính 40 mm. Chọn B trên đường tròn A; vẽ đường tròn B có đường kính 8 cm. Bạn viết: “Lần cuối mở compa 8 cm, hai lần đầu 4 cm.” Giữ câu ấy; sửa nếu cần, cho biết có phải đổi độ mở giữa các lần và kiểm điều kiện tâm. Không có ảnh bản vẽ.',
 'Độ mở đúng và phản hồi câu viết',[
 st('Đổi hai bán kính đầu','Một mét bằng 100 cm,10 mm bằng 1 cm.','4 cm và 4 cm','0,04 m=4 cm;40 mm=4 cm. A và B phải nằm trên đúng đường tròn trước.','4/100*100','cm'),
 st('Phân biệt đường kính','Độ mở compa là bán kính, bằng nửa đường kính.','4','Lần cuối 8:2=4 cm; giữ cùng độ mở cả ba lần. Câu bạn đúng hai lần đầu, sai lần cuối.','8/2','cm'),
 st('Kiểm phạm vi','Chỉ có câu viết và điều kiện mô hình.','OA=AB=4 cm; bán kính đường tròn B=4 cm','Không suy OB=4 cm, không chứng nhận nét vẽ thực khi chưa có ảnh hay quan sát.')],
 [('Độ mở mỗi lần','4','cm'),('Đổi độ mở','Không','')],dict(kind='circle_same',first_m='0.04',second_mm='40',diameter_cm='8',opening='4'),
 'Same compass opening under mixed radius/diameter units; observable quote only.',
 'Lần cuối mở compa 8 cm, hai lần đầu 4 cm.')
 m=W[5]
 put(m,'g4_acute_diagonal_grid_ray',4,
 'Lưới ô vuông có O ở một giao điểm, tia OA ngang sang phải. B cách O 3 ô sang phải,3 ô lên trên. Bài cho tính chất: đường chéo ô vuông chia góc vuông tại đỉnh thành hai góc bằng nhau. Vẽ tia OB bằng thước thẳng, xác định góc AOB nhỏ hơn góc bẹt và nêu cách kiểm bằng thước đo góc nếu có. Không khẳng định đã dùng dụng cụ thật.',
 'Dựng tia không vuông và kiểm góc',[
 st('Định vị đúng tia','Bước ngang và dọc bằng nhau nên OB cùng phương đường chéo ô vuông.','Nối O qua B thành tia OB','Đặt thước qua O,B, kéo về phía lên phải; không tự thay B bằng điểm lệch số ô.'),
 st('Dùng tính chất được cho','Đường chéo chia đều góc vuông.','45','90:2=45 độ, góc nhọn. Đây là góc mở nhỏ giữa OA và OB.','90/2','độ'),
 st('Kiểm dụng cụ theo kế hoạch','Tâm thước ở O,vạch 0 cùng phía OA; đọc đúng thang lên B.','Kiểm vạch 45 độ','Nếu quan sát thực lệch thì cần chỉnh hoặc ảnh rõ; chưa có quan sát thì chỉ kết luận mô hình.')],
 [('Góc AOB','45','độ')],dict(kind='grid_angle',v1=[1,0],v2=[3,3],angle=45),
 'Prescribed nonright grid ray with supplied exact square-diagonal relation.')
 put(m,'g4_obtuse_diagonal_opposite_scale',4,
 'OA ngang sang phải trên lưới ô vuông. C cách O 2 ô sang trái,2 ô lên trên. Cho đường chéo ô vuông tạo với cạnh kề góc bằng nửa góc vuông. Cần vẽ OC, đo góc AOC ở phía trên nhỏ hơn góc bẹt. Bạn ghi: “Em đọc 45 độ vì thấy đường chéo.” Giữ câu này; nêu góc đúng,cách đặt thước và chọn thang.',
 'Góc tù và kiểm tia gốc',[
 st('Giữ hướng gốc','OA hướng phải còn OC hướng lên trái.','Hai tia khác phía ngang','OC tạo góc nhọn với tia ngang trái; tia đó không phải OA.'),
 st('Dùng góc kề bù','Từ ngang phải tới ngang trái phía trên là góc bẹt.','135','180−45=135 độ là góc AOC phía trên. Câu bạn lấy góc kề với tia ngang trái.','180-45','độ'),
 st('Kiểm chọn thang','Tâm ở O,vạch 0 bên phải theo OA, đọc lên phía C.','135 độ là góc tù','Không suy nghĩ kín của bạn từ câu viết; cần ảnh để nhận xét cách cầm và đặt thước thật.')],
 [('Góc AOC','135','độ')],dict(kind='grid_angle',v1=[1,0],v2=[-2,2],angle=135),
 'Obtuse rotated grid ray plus grounded wrong-scale feedback.', 'Em đọc 45 độ vì thấy đường chéo.')
 m=W[6]
 put(m,'orthogonal_half_folds_uniform_layers',5,
 'Bản đồ chữ nhật 24 cm×16 cm. Gấp mép trái trùng phải rồi gấp mép dưới trùng trên của phần đang chồng, mỗi lần đúng nửa; không cắt,bỏ qua độ dày. Tìm kích thước và diện tích dấu chân nhìn thẳng từ trên,số lớp ở mọi điểm trong dấu chân và diện tích giấy ban đầu; không tính cả hai mặt giấy.',
 'Dấu chân và diện tích có tính lớp',[
 st('Theo dõi từng chiều','Lần đầu chia đôi ngang,lần sau chia đôi dọc.','12 cm×8 cm','Sau lần đầu 12×16, sau lần hai 12×8; không chia cả hai chiều ở mỗi lần.'),
 st('Đếm lớp và dấu chân','Mỗi lần gấp đôi nhân đôi số lớp.','96','Dấu chân 12×8=96 cm², có 4 lớp trong mọi miền có diện tích; bỏ qua đường nếp có diện tích bằng không.','12*8','cm²'),
 st('Kiểm bảo toàn','Diện tích dấu chân nhân đúng số lớp trả lại lượng giấy.','384','4×96=384 cm², khớp 24×16. Diện tích nhìn nhỏ không có nghĩa giấy mất đi.','4*96','cm²')],
 [('Kích thước dấu chân','12×8','cm'),('Dấu chân','96','cm²'),('Lớp','4','lớp'),('Ban đầu','384','cm²')],dict(kind='fold_uniform',w='24',h='16',folds=2,footprint='96',layers=4,original='384'),
 'Two oriented half folds; original sheet versus visible footprint.')
 put(m,'offcenter_then_half_nonuniform_layers',5,
 'Giấy rộng 12 cm,cao 6 cm. Gấp dải trái rộng 4 cm sang phải theo nếp cách mép trái 4 cm; nó phủ dải vị trí ban đầu 4–8 cm. Phần nằm phẳng ngang từ 4 đến 12 cm: dải 4–8 có 2 lớp,dải 8–12 có 1 lớp. Sau đó gấp nửa dưới phần này trùng nửa trên theo chiều cao. Không cắt,bỏ qua dày. Tính dấu chân cuối,số lớp từng dải và kiểm diện tích giấy.',
 'Dấu chân có lớp không đồng đều',[
 st('Giữ đúng nếp đầu','Nếp đầu không ở giữa nên bề ngang không chia hai.','Rộng 8 cm','Phần nằm phẳng từ vị trí 4 đến 12 dài 8 cm; mỗi dải rộng 4 cm.'),
 st('Gấp theo cao','Chiều cao chia hai; số lớp từng dải nhân đôi.','24','Cao 3 cm, dấu chân 8×3=24 cm²; dải 4–8 có 4 lớp,dải 8–12 có 2 lớp.','8*3','cm²'),
 st('Kiểm theo từng miền','Mỗi dải có diện tích 4×3=12 cm² nhưng số lớp khác nhau.','72','12×4+12×2=72 cm² bằng 12×6 ban đầu. Không lấy 24×4 vì không đều lớp.','12*4+12*2','cm²')],
 [('Dấu chân','8×3','cm'),('Diện tích dấu chân','24','cm²'),('Hai dải','4 lớp;2 lớp',''),('Giấy ban đầu','72','cm²')],dict(kind='fold_nonuniform',w=12,h=6,first_flap=4,bands=[[4,4],[4,2]],final_h=3,footprint=24,total=72),
 'Off-center fold followed by half fold, regionwise layer conservation.')
 m=W[7]
 put(m,'vertical_base_two_completions',5,
 'Lưới ô vuông: A cột 1 hàng 1,B cột 1 hàng 5,C cột 4 hàng 4; chưa có D. Chỉ chọn D trong P cột 4 hàng 1,Q cột 4 hàng 2,R cột 3 hàng 1. Nối A–B–C–D–A theo thứ tự. Bài quy ước hình thang có đúng một cặp cạnh đối song song,không tự cắt. Tìm mọi D để AB và CD là đáy; không tự thêm điểm.',
 'Hoàn thiện hình thang đáy dọc trong miền hữu hạn',[
 st('Nhận phương đáy','AB cùng cột nên CD cũng phải thẳng đứng.','D cần cùng cột C','Giữ thứ tự đỉnh để xét đúng cạnh đối AB,CD.'),
 st('Thử mọi điểm','P,Q cùng cột 4;R không cùng cột C.','D=P hoặc D=Q','Hai tứ giác đều không tự cắt. Với P,AD ngang còn BC xiên; với Q,AD lên phải,BC xuống phải nên không song song.'),
 st('Kiểm đầy đủ','Danh sách chỉ ba điểm nên loại R hoàn tất xét miền.','Hai cách hợp lệ','Không tự kết luận có duy nhất một D khi P và Q đều đáp ứng; hướng dọc của đáy không làm mất hình thang.')],
 [('Mọi D','P và Q','')],dict(kind='trapezoid',A=[1,1],B=[1,5],C=[4,4],candidates={'P':[4,1],'Q':[4,2],'R':[3,1]},valid=['P','Q']),
 'Incomplete vertical-base figure with two alternative completions.')
 put(m,'diagonal_base_exclusive_trapezoid',5,
 'Lưới ô vuông: A cột 1 hàng 1,B cột 3 hàng 3,C cột 6 hàng 3; chưa có D. Chỉ chọn D trong P cột 5 hàng 2,Q cột 4 hàng 1,R cột 5 hàng 1. Nối A–B–C–D–A. Muốn AB song song CD và quy ước bài này hình thang có đúng một cặp cạnh đối song song. Tìm mọi D hợp lệ,nêu phương án bị loại dù AB song song CD.',
 'Hoàn thiện đáy xiên và kiểm quy ước',[
 st('Dùng bước lưới','AB sang phải 2,lên 2 nên đường song song có bước ngang bằng bước dọc cùng hướng.','P,Q cho CD song song AB','Từ P tới C sang phải 1 lên 1;từ Q tới C sang phải 2 lên 2. R tới C sang phải 1 lên 2 nên không song song.'),
 st('Kiểm cặp cạnh còn lại','Đúng một cặp nghĩa là phải loại trường hợp cả hai cặp song song.','Chỉ P đạt','Với Q,AD và BC cùng ngang nên hình bình hành,bị loại theo quy ước đã cho. Với P,AD xiên còn BC ngang.'),
 st('Kiểm miền và hình','A–B–C–P–A không tự cắt.','P duy nhất trong danh sách','Không nói mọi định nghĩa hình thang đều loại hình bình hành; ở đây quy ước được ghi rõ.')],
 [('D hợp lệ','P',''),('Q','Bị loại vì hai cặp cạnh đối song song','')],dict(kind='trapezoid',A=[1,1],B=[3,3],C=[6,3],candidates={'P':[5,2],'Q':[4,1],'R':[5,1]},valid=['P']),
 'Rotated diagonal incomplete figure and explicit exclusive convention.')
 m=W[8]
 put(m,'g3_rectangle_single_cut_to_square',3,
 'Giấy chữ nhật 8 cột,2 hàng ô vuông cạnh 1 cm. Chỉ cắt một lần theo giữa cột 4 và 5,được hai miếng bằng nhau. Không cắt thêm,được chuyển và xoay,không chồng hay để khe. Mô tả cách ghép hình vuông,tính diện tích và so chu vi trước sau.',
 'Đường cắt,ghép và kiểm diện tích/chu vi',[
 st('Nhận hai miếng','Đường giữa chia 8 cột thành hai nhóm 4 cột.','Hai miếng 4×2 cm','Cắt hết chiều cao,không mất giấy.'),
 st('Ghép đúng hai phía','Đặt hai cạnh dài 4 cm trùng nhau,hai miếng nằm hai phía của cạnh ghép.','Vuông cạnh 4 cm','Ngang 4,cao 2+2=4. Hai miếng chỉ chung đường biên nên không chồng diện tích,không khe.'),
 st('Kiểm hai đại lượng riêng','Chuyển mảnh giữ diện tích nhưng đổi biên ngoài.','16','Diện tích 8×2=16 bằng 4×4 cm². Chu vi cũ (8+2)×2=20 cm,mới 4×4=16 cm; diện tích không đổi không buộc chu vi giữ.','8*2','cm²')],
 [('Hình mới','Vuông cạnh 4 cm',''),('Diện tích','16','cm²'),('Chu vi trước/sau','20;16','cm')],dict(kind='rect_cut',w=8,h=2,pieces=[[4,2],[4,2]],new=[4,4],area=16,perimeters=[20,16]),
 'G3 explicit one-cut square reassembly with changed perimeter.')
 put(m,'g4_parallelogram_cut_translate',4,
 'Hình bình hành trên lưới: đáy AB ngang dài 6 ô; D cao 3 ô,lệch phải 2 ô so với A; C cao 3 ô,lệch phải 2 ô so với B. Hạ vuông góc từ D tới AB tại E,AE=2 ô. Cắt tam giác AED, chuyển sang phải đúng 6 ô cho A trùng B,E tới F trên tia AB với BF=2 ô,D trùng C. Không xoay. Mỗi ô cạnh 1 cm. Mô tả hình ghép,kiểm kín và không chồng,tính diện tích.',
 'Cắt chuyển với cạnh tương ứng và kiểm diện tích',[
 st('Theo dõi mảnh chuyển','Tam giác AED có hai cạnh vuông góc 2 cm và 3 cm.','AED chuyển thành BFC','Các đỉnh A→B,E→F,D→C theo cùng một phép chuyển ngang 6 ô,giữ toàn mảnh.'),
 st('Kiểm miền ghép','Bỏ mảnh trái làm mép trái qua E,D; thêm BFC lấp đúng khoảng bên phải.','Chữ nhật từ E đến F,rộng 6 cm,cao 3 cm','Phần chuyển và phần còn chỉ chung biên BC,không chồng miền trong. Biên trên DC và dưới EF cùng dài 6 cm.'),
 st('Kiểm diện tích','Cắt chuyển đủ phần không hao hụt bảo toàn diện tích.','18','6×3=18 cm². Mảnh chuyển 2×3:2=3 cm² đúng chỗ lấp; không lấy cạnh xiên làm chiều cao.','6*3','cm²')],
 [('Hình mới','Chữ nhật 6×3 cm',''),('Diện tích','18','cm²')],dict(kind='par_cut',A=[0,0],B=[6,0],C=[8,3],D=[2,3],E=[2,0],F=[8,0],shift=[6,0],area=18),
 'G4 exact parallelogram triangle translation, unlike accepted G5 trapezoid cuts.')
 put(m,'g4_square_diagonal_pair_reassembly',4,
 'Giấy vuông ABCD cạnh 4 cm,cắt theo cả hai đường chéo tại O,được bốn tam giác bằng nhau. Ghép từng cặp theo cạnh huyền: hai cạnh huyền trùng trọn,hai mảnh nằm hai phía cạnh ghép; mỗi cặp tạo một hình vuông. Đặt hai hình vuông mới cạnh nhau,chung trọn một cạnh và ở hai phía cạnh đó. Không cắt thêm,chồng hoặc để khe. Mô tả tỉ lệ dài:rộng của hình cuối,diện tích và giải thích vì sao cạnh của hình vuông mới không bằng cạnh giấy ban đầu. Không yêu cầu tính số vô tỉ.',
 'Ghép bốn tam giác theo cạnh và kiểm diện tích',[
 st('Nhận cạnh tam giác','Hai đường chéo vuông góc và chia đôi nhau nên mỗi tam giác vuông cân tại O.','Bốn tam giác bằng nhau','Mỗi tam giác diện tích một phần tư giấy. Cạnh huyền dài 4 cm,cạnh góc vuông là nửa đường chéo giấy.'),
 st('Ghép theo cạnh huyền','Hai tam giác vuông cân chung cạnh huyền ở hai phía tạo hình vuông.','Hai hình vuông nhỏ,cạnh bằng nửa đường chéo cũ','Cạnh huyền nằm bên trong hình vuông mới; cạnh góc vuông thành cạnh ngoài. Vì thế không lấy cạnh huyền 4 cm làm cạnh vuông mới.'),
 st('Kiểm kín hình và diện tích','Hai vuông chung trọn cạnh,không chồng phần trong,tạo chữ nhật.','Dài:rộng=2:1;diện tích 16 cm²','Mỗi vuông chứa hai tam giác nên có 8 cm²;hai vuông có 16 cm²,bằng 4×4 ban đầu. Hai chiều là hai lần cạnh vuông mới và một lần cạnh ấy.','4*4','cm²')],
 [('Tỉ lệ dài:rộng','2:1',''),('Diện tích','16','cm²'),('Cạnh vuông mới','Nửa đường chéo giấy ban đầu','')],dict(kind='square_diagonal',side=4,triangles=4,area=16,joint='hypotenuse',ratio=[2,1]),
 'G4 square-diagonal dissection exact hypotenuse adjacency and pair conservation.')
 m=W[9]
 put(m,'wheel_cm_to_m_fractional_turns',5,
 'Bánh xe đường kính 40 cm lăn thẳng không trượt 12,5 vòng. Dùng 3,14,bỏ qua biến dạng. Tính đường đi bằng mét,giữ phần nửa vòng; không dùng diện tích hình tròn.',
 'Quãng đường đổi từ cm sang m',[
 st('Độ dài một vòng','Lăn không trượt,mỗi vòng đi một chu vi bánh.','125.6','3,14×40=125,6 cm;đã cho đường kính nên không nhân đôi thêm.','314/100*40','cm'),
 st('Nhân số vòng','Nửa vòng đi nửa chu vi,không bỏ phần lẻ.','1570','125,6×12,5=1570 cm.','1256/10*125/10','cm'),
 st('Đổi và kiểm','100 cm bằng 1 m.','15.7','1570:100=15,7 m. Đổi ngược 15,7 m thành 1570 cm,rồi chia chu vi được 12,5 vòng.','1570/100','m')],
 [('Đường đi','15.7','m')],dict(kind='wheel',diameter_cm='40',turns='12.5',pi='3.14',distance_m='15.7'),
 'Mixed-unit rolling distance residual with fractional turn retained.')
 put(m,'wheel_inverse_km_dm_radius',5,
 'Bánh xe bán kính 2,5 dm lăn không trượt trên đường thẳng dài 0,157 km. Dùng 3,14,bỏ qua biến dạng,tính cả vòng lẻ nếu có. Bạn viết “0,157 : 3,14 : 2,5”. Giữ phép viết ấy; tính số vòng và kiểm theo cùng đơn vị,chỉ nhận xét điều đã viết.',
 'Số vòng từ km và dm,kiểm bán kính',[
 st('Đổi cùng đơn vị','0,157 km=157 m;2,5 dm=0,25 m.','1.57','Chu vi 2×3,14×0,25=1,57 m. Phép bạn trộn km với dm,còn thiếu nhân đôi bán kính.','2*314/100*25/100','m'),
 st('Lấy đường đi chia một vòng','Cùng đơn vị mét cho thương là số vòng.','100','157:1,57=100 vòng;không dùng diện tích đĩa làm đường đi.','157/(157/100)','vòng'),
 st('Kiểm ngược','Số vòng nhân chu vi phải về quãng đường đã cho.','157 m=0,157 km','100×1,57=157 m. Không suy cách nghĩ ngoài biểu thức hoặc nhận xét bánh thật khi chưa có quan sát.')],
 [('Số vòng','100','vòng')],dict(kind='wheel_inverse',radius_dm='2.5',distance_km='0.157',pi='3.14',turns='100'),
 'Inverse rolling turns with km/dm conversion and radius-diameter distinction.', '0,157 : 3,14 : 2,5')
