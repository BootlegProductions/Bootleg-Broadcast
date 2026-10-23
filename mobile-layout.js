/* Keep the CRT feet on the room's tabletop as browser chrome and orientation change. */
(() => {
  const stage=document.getElementById('stage'),tv=document.getElementById('tv-container'),remote=document.getElementById('remote-control');
  const root=document.documentElement;
  let wasMobile=false,frame=0;
  function measure(){
    frame=0;
    const {width:w,height:h}=stage.getBoundingClientRect();
    const mobile=w<=1400&&(w<=1180||h<=1100||matchMedia('(pointer: coarse)').matches);
    document.body.classList.toggle('mobile-scene',mobile);
    if(!mobile){document.body.classList.remove('scene-portrait','scene-landscape');wasMobile=false;return;}
    const portrait=h>=w;
    document.body.classList.toggle('scene-portrait',portrait);
    document.body.classList.toggle('scene-landscape',!portrait);
    // The art is unchanged. Match its cover crop so the TV rests on the table.
    const phone=portrait&&w<=700;
    const image=portrait?(phone?{w:1080,h:1920,table:960}:{w:1536,h:2048,table:1030}):{w:1920,h:1080,table:1060};
    const scale=Math.max(w/image.w,h/image.h);
    const table=image.table*scale-(image.h*scale-h)/2;
    const margin=12;
    const remoteWidth=Math.min(portrait?248:224,w-2*margin);
    const reserved=portrait?0:remoteWidth+24;
    const availableWidth=w-reserved-2*margin;
    const ratio=portrait?488/666:1154/1258;
    const bottom=Math.min(h-16,Math.max(130,table));
    const maxHeight=Math.max(100,bottom-54);
    const tvWidth=Math.min(portrait?Math.min(w*.94,w-2*margin):availableWidth,maxHeight/ratio,portrait?850:920);
    const tvHeight=tvWidth*ratio;
    const left=portrait?(w-tvWidth)/2:reserved+(w-reserved-tvWidth)/2;
    const top=bottom-tvHeight;
    root.style.setProperty('--mobile-tv-width',`${tvWidth}px`);
    root.style.setProperty('--mobile-tv-left',`${left}px`);
    root.style.setProperty('--mobile-tv-top',`${top}px`);
    root.style.setProperty('--mobile-remote-width',`${remoteWidth}px`);
    root.style.setProperty('--mobile-remote-height',`${Math.max(120,portrait?h-bottom-65:h-72)}px`);
    if(!wasMobile){remote.classList.remove('active');document.getElementById('remote-handle').setAttribute('aria-expanded','false');}
    wasMobile=true;
  }
  function schedule(){if(!frame)frame=requestAnimationFrame(measure);}
  window.addEventListener('resize',schedule);
  window.addEventListener('orientationchange',schedule);
  window.visualViewport?.addEventListener('resize',schedule);
  new ResizeObserver(schedule).observe(stage);
  measure();
})();
