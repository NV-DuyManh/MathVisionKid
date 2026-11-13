/** Flag only explicit source gaps; confirmation never supplies a missing fact. */
export function sourceClarification(source: string): { message: string; mixedPreview?: string } | null {
  const fold = (text: string) => text.toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const text = fold(source);
  if (/\(\s*\?\s*\)\s*[/⁄]\s*(?:\d+|\(\s*(?:\d+|\?)\s*\))|(?:\d+|\(\s*\d+\s*\))\s*[/⁄]\s*\(\s*\?\s*\)/.test(text)) return {
    message: 'Có phân số chưa đọc rõ. Em đối chiếu với ảnh rồi điền đủ tử số và mẫu số. Nếu ảnh bị cắt, em chọn lại vùng bài toán nhé.',
  };
  if (/\d\(\s*\d+\s*(?:\/|\)\s*\/)/.test(text)) return {
    message: 'Phần nguyên đang dính vào phân số. Em nhìn lại ảnh: đây là các hỗn số hay phép nhân? Chỉ tách thành hỗn số khi đúng với ảnh.',
    mixedPreview: source.replace(/(\d)(?=\(\s*\d+\s*(?:\/|\)\s*\/))/g, '$1 '),
  };
  if (/\bm(?:²|\^2|2)(?!\w)/.test(text)
    && /thu hoach duoc\s+(?:\(\s*\d+\s*\)|\d+)\s*\/\s*(?:\(\s*\d+\s*\)|\d+)\s+thoc\b/.test(text)
    && /bao nhieu\s+(?:ta|kg|ki[ -]lo)/.test(text)) return {
    message: 'Đề chưa ghi đơn vị của lượng thóc thu hoạch trên mỗi mét vuông. Em kiểm tra đề gốc hoặc hỏi người ra đề rồi bổ sung đơn vị; mình chưa tự chọn kg hay g nhé.',
  };
  const stem = fold(source.split(/(?<!\w)A[.)]/, 1)[0]);
  if (/lam tron den\s+\d/.test(stem) && !/hang\s+|so tu nhien|gan nhat/.test(stem)) return {
    message: 'Đề chưa nói làm tròn đến hàng nào. Em kiểm tra đề gốc hoặc hỏi người ra đề rồi bổ sung yêu cầu, chẳng hạn hàng đơn vị hoặc hàng phần mười.',
  };
  return null;
}
