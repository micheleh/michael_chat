import React from 'react';

interface ImageThumbnailProps {
  image: {
    id: string;
    file: File;
    url: string;
    name: string;
    size: number;
  };
  onRemove: (id: string) => void;
  showRemoveButton?: boolean;
}

const ImageThumbnail: React.FC<ImageThumbnailProps> = ({ 
  image, 
  onRemove, 
  showRemoveButton = true 
}) => {
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="image-thumbnail">
      <div className="image-thumbnail-container">
        <img 
          src={image.url} 
          alt={image.name}
          className="image-thumbnail-image"
        />
        {showRemoveButton && (
          <button 
            onClick={() => onRemove(image.id)}
            className="image-thumbnail-remove"
            title="Remove image"
          >
            ×
          </button>
        )}
      </div>
      <div className="image-thumbnail-info">
        <div className="image-thumbnail-name" title={image.name}>
          {image.name}
        </div>
        <div className="image-thumbnail-size">
          {formatFileSize(image.size)}
        </div>
      </div>
    </div>
  );
};

export default ImageThumbnail;
