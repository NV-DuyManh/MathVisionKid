export function pickWebPhoto(capture: boolean): Promise<File | undefined> {
  return new Promise(resolve => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.hidden = true;
    if (capture) input.setAttribute('capture', 'environment');

    const finish = () => {
      const photo = input.files?.[0];
      input.remove();
      resolve(photo);
    };
    input.addEventListener('change', finish, { once: true });
    input.addEventListener('cancel', finish, { once: true });
    document.body.append(input);
    input.click();
  });
}
