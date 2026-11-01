import React, { useRef } from 'react';
import type { SliderProps } from '@react-native-community/slider';

/** Browser-native range provides continuous pointer/touch scrubbing and keyboard controls. */
export default function MediaSlider({ value = 0, minimumValue = 0, maximumValue = 1, disabled, accessibilityLabel,
  onSlidingStart, onValueChange, onSlidingComplete }: SliderProps) {
  const interacting = useRef(false);
  const begin = () => { if (!interacting.current) { interacting.current = true; onSlidingStart?.(value); } };
  const finish = (element: HTMLInputElement) => {
    if (interacting.current) { interacting.current = false; onSlidingComplete?.(Number(element.value)); }
  };
  const progress = (value - minimumValue) / (maximumValue - minimumValue || 1) * 100;
  return <>
    <style>{`.mv-media-slider{appearance:none;-webkit-appearance:none;background:transparent;width:100%;height:48px;margin:0;cursor:pointer;touch-action:pan-y}.mv-media-slider:disabled{cursor:default;opacity:.45}.mv-media-slider:focus-visible{outline:2px solid #7950DA;outline-offset:3px;border-radius:10px}.mv-media-slider::-webkit-slider-runnable-track{height:5px;border-radius:8px;background:linear-gradient(to right,#7650E6 var(--fill),#E4DDF3 var(--fill))}.mv-media-slider::-webkit-slider-thumb{appearance:none;-webkit-appearance:none;width:18px;height:18px;margin-top:-6.5px;border:3px solid white;border-radius:50%;background:#7650E6;box-shadow:0 1px 5px #56378B45}.mv-media-slider::-moz-range-track{height:5px;border-radius:8px;background:#E4DDF3}.mv-media-slider::-moz-range-progress{height:5px;border-radius:8px;background:#7650E6}.mv-media-slider::-moz-range-thumb{width:13px;height:13px;border:3px solid white;border-radius:50%;background:#7650E6}`}</style>
    <input className="mv-media-slider" type="range" min={minimumValue} max={maximumValue} step={0.05} value={value} disabled={disabled}
      aria-label={accessibilityLabel} aria-valuetext={`${value.toFixed(1)} trên ${maximumValue.toFixed(1)} giây`}
      style={{ '--fill': `${progress}%` } as React.CSSProperties}
      onPointerDown={begin} onPointerUp={event => finish(event.currentTarget)} onPointerCancel={event => finish(event.currentTarget)}
      onChange={event => { if (interacting.current) onValueChange?.(Number(event.currentTarget.value)); }}
      onKeyDown={event => { if (['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End','PageUp','PageDown'].includes(event.key)) begin(); }}
      onKeyUp={event => finish(event.currentTarget)} onBlur={event => finish(event.currentTarget)} />
  </>;
}
