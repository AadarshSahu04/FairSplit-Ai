/**
 * BillUploader.jsx
 *
 * Phase 3: Drag-drop upload zone with image previews.
 * Supports up to 4 images (for long bills that span multiple photos).
 */
import { useCallback, useRef, useState } from 'react';
import { Alert, Button, Spinner } from '../ui/index.jsx';
import './BillUploader.css';

const MAX_IMAGES = 4;
const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp', 'image/heic'];

export function BillUploader({ billImages, addImages, removeImage, runExtraction, extractionStatus, extractionError }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const addMoreRef = useRef(null);

  const isLoading = extractionStatus === 'loading';
  const canAdd    = billImages.length < MAX_IMAGES;

  const filterFiles = (files) =>
    Array.from(files).filter((f) => ACCEPTED.includes(f.type)).slice(0, MAX_IMAGES - billImages.length);

  const onDragEnter = useCallback((e) => { e.preventDefault(); setDragging(true);  }, []);
  const onDragLeave = useCallback((e) => { e.preventDefault(); setDragging(false); }, []);
  const onDragOver  = useCallback((e) => { e.preventDefault(); },                    []);
  const onDrop      = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const files = filterFiles(e.dataTransfer.files);
    if (files.length) addImages(files);
  }, [billImages.length, addImages]); // eslint-disable-line

  const onFileChange = useCallback((e) => {
    const files = filterFiles(e.target.files);
    if (files.length) addImages(files);
    e.target.value = '';
  }, [billImages.length, addImages]); // eslint-disable-line

  const openPicker = () => inputRef.current?.click();

  const hasImages = billImages.length > 0;

  return (
    <div className="uploader">
      <div
        className={[
          'uploader__dropzone',
          dragging ? 'uploader__dropzone--dragover' : '',
          hasImages ? 'uploader__dropzone--has-files' : '',
        ].filter(Boolean).join(' ')}
        onDragEnter={onDragEnter}
        onDragLeave={onDragLeave}
        onDragOver={onDragOver}
        onDrop={onDrop}
        onClick={hasImages ? undefined : openPicker}
        role="button"
        tabIndex={hasImages ? -1 : 0}
        aria-label={hasImages ? 'Drop zone with uploaded images' : 'Click or drag to upload bill images'}
        onKeyDown={(e) => e.key === 'Enter' && openPicker()}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(',')}
          multiple
          className="uploader__file-input"
          onChange={onFileChange}
          id="bill-file-input"
          aria-label="Upload bill images"
          style={{ pointerEvents: hasImages ? 'none' : 'auto' }}
        />

        {!hasImages ? (
          <>
            <div className="uploader__icon">🧾</div>
            <div>
              <p className="uploader__title">Drop your bill here</p>
              <p className="uploader__subtitle">or click to browse files</p>
            </div>
            <p className="uploader__formats">JPG, PNG, WebP, HEIC — up to {MAX_IMAGES} images</p>
          </>
        ) : (
          <div className="uploader__previews">
            {billImages.map((file, idx) => {
              const url = URL.createObjectURL(file);
              return (
                <div key={idx} className="uploader__preview-item">
                  <img
                    src={url}
                    alt={`Bill image ${idx + 1}`}
                    className="uploader__preview-img"
                    onLoad={() => URL.revokeObjectURL(url)}
                  />
                  <button
                    className="uploader__preview-remove"
                    onClick={(e) => { e.stopPropagation(); removeImage(idx); }}
                    aria-label={`Remove image ${idx + 1}`}
                    type="button"
                  >
                    ×
                  </button>
                  <div className="uploader__preview-name">{file.name}</div>
                </div>
              );
            })}

            {canAdd && (
              <button
                className="uploader__add-more"
                onClick={(e) => { e.stopPropagation(); addMoreRef.current?.click(); }}
                type="button"
                aria-label="Add more images"
              >
                <input
                  ref={addMoreRef}
                  type="file"
                  accept={ACCEPTED.join(',')}
                  multiple
                  style={{ display: 'none' }}
                  onChange={onFileChange}
                />
                <span className="uploader__add-more-icon">+</span>
                <span>Add more</span>
              </button>
            )}
          </div>
        )}
      </div>

      {extractionError && (
        <div className="uploader__error">
          <Alert variant="error">{extractionError}</Alert>
        </div>
      )}

      {hasImages && (
        <div className="uploader__actions">
          <Button
            id="btn-extract-bill"
            variant="primary"
            size="lg"
            disabled={isLoading}
            onClick={runExtraction}
          >
            {isLoading ? (
              <><Spinner /> Extracting bill…</>
            ) : (
              <>✨ Extract Bill</>
            )}
          </Button>

          {!isLoading && (
            <p className="uploader__hint">
              {billImages.length === 1 ? '1 image ready' : `${billImages.length} images ready`}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
