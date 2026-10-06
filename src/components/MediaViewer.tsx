import { useState } from 'react';
import { X, Download, ZoomIn, ZoomOut } from 'lucide-react';
import { useStore } from '../stores';

export default function MediaViewer() {
  const { showMediaViewer, selectedMedia, setMediaViewer, messages } = useStore();
  const [scale, setScale] = useState(1);

  if (!showMediaViewer || !selectedMedia) return null;

  const handleDownload = () => {
    const a = document.createElement('a');
    a.href = selectedMedia.url;
    a.download = 'file';
    a.click();
  };

  const handleZoomIn = () => setScale(s => Math.min(s + 0.5, 5));
  const handleZoomOut = () => setScale(s => Math.max(s - 0.5, 0.5));

  return (
    <div className="media-viewer animate-fade-in" onClick={() => { setMediaViewer(false); setScale(1); }}>
      {/* Close button */}
      <button className="absolute top-4 right-4 p-2 rounded-full z-10" style={{ background: 'rgba(0,0,0,0.5)' }}
        onClick={(e) => { e.stopPropagation(); setMediaViewer(false); setScale(1); }}>
        <X size={24} color="white" />
      </button>

      {/* Controls */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-3 z-10">
        <button className="p-2 rounded-full" style={{ background: 'rgba(0,0,0,0.5)' }} onClick={(e) => { e.stopPropagation(); handleZoomOut(); }}>
          <ZoomOut size={20} color="white" />
        </button>
        <button className="p-2 rounded-full" style={{ background: 'rgba(0,0,0,0.5)' }} onClick={(e) => { e.stopPropagation(); handleDownload(); }}>
          <Download size={20} color="white" />
        </button>
        <button className="p-2 rounded-full" style={{ background: 'rgba(0,0,0,0.5)' }} onClick={(e) => { e.stopPropagation(); handleZoomIn(); }}>
          <ZoomIn size={20} color="white" />
        </button>
      </div>

      {/* Media content */}
      <div className="flex items-center justify-center w-full h-full" onClick={e => e.stopPropagation()}>
        {selectedMedia.type === 'image' ? (
          <img
            src={selectedMedia.url}
            alt=""
            className="max-w-full max-h-full object-contain transition-transform"
            style={{ transform: `scale(${scale})` }}
          />
        ) : selectedMedia.type === 'video' ? (
          <video
            src={selectedMedia.url}
            controls
            autoPlay
            className="max-w-full max-h-full"
          />
        ) : null}
      </div>
    </div>
  );
}
