import { useState, useRef, useCallback } from 'react';
import { Button, Card, CardBody, CardTitle, Label, Split, SplitItem, Alert } from '@patternfly/react-core';
import { UploadIcon, TimesIcon, FileIcon, CodeIcon, ImageIcon, VolumeUpIcon } from '@patternfly/react-icons';

interface UploadedDoc {
  id: string;
  filename: string;
  modality: string;
  category: string;
  chunk_count: number;
  content_warnings?: string[];
}

interface Props {
  documents: UploadedDoc[];
  onUpload: (file: File) => Promise<void>;
  onDelete: (id: string) => void;
}

const ALLOWED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.py', '.yaml', '.yml', '.json', '.png', '.jpg', '.jpeg', '.mp3', '.wav'];

const MODALITY_ICONS: Record<string, React.ReactNode> = {
  text: <FileIcon />,
  code: <CodeIcon />,
  image: <ImageIcon />,
  audio: <VolumeUpIcon />,
};

const MODALITY_COLORS: Record<string, 'blue' | 'orange' | 'green' | 'purple'> = {
  text: 'blue',
  code: 'green',
  image: 'orange',
  audio: 'purple',
};

export default function DocumentUploader({ documents, onUpload, onDelete }: Props) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    setError('');
    for (const file of Array.from(files)) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setError(`File type not allowed: ${file.name}`);
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError(`File too large: ${file.name} (max 10MB)`);
        continue;
      }
      setUploading(true);
      try {
        await onUpload(file);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Upload failed');
      }
      setUploading(false);
    }
  }, [onUpload]);

  return (
    <Card isCompact>
      <CardTitle>Documents</CardTitle>
      <CardBody>
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
          onClick={() => inputRef.current?.click()}
          style={{
            border: `2px dashed ${dragOver ? 'var(--pf-t--global--border--color--hover)' : 'var(--pf-t--global--border--color--default)'}`,
            borderRadius: '8px',
            padding: '1.5rem',
            textAlign: 'center',
            cursor: 'pointer',
            marginBottom: documents.length > 0 ? '1rem' : 0,
            background: dragOver ? 'var(--pf-t--global--background--color--primary--hover)' : 'transparent',
          }}
        >
          <UploadIcon style={{ marginRight: '0.5rem' }} />
          {uploading ? 'Uploading...' : 'Drop files here or click to upload'}
          <div style={{ fontSize: '0.8rem', color: 'var(--pf-t--global--text--color--subtle)', marginTop: '0.25rem' }}>
            PDF, TXT, MD, Python, YAML, JSON, images, audio (max 10MB)
          </div>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={ALLOWED_EXTENSIONS.join(',')}
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
            style={{ display: 'none' }}
          />
        </div>

        {error && <Alert variant="danger" title={error} isInline style={{ marginBottom: '0.5rem' }} />}

        {documents.map((doc) => (
          <Split key={doc.id} hasGutter style={{ padding: '0.35rem 0', alignItems: 'center' }}>
            <SplitItem>{MODALITY_ICONS[doc.modality] || <FileIcon />}</SplitItem>
            <SplitItem isFilled>{doc.filename}</SplitItem>
            <SplitItem><Label isCompact color={MODALITY_COLORS[doc.modality] || 'grey'}>{doc.modality}</Label></SplitItem>
            <SplitItem><Label isCompact>{doc.category}</Label></SplitItem>
            <SplitItem><Label isCompact>{doc.chunk_count} chunks</Label></SplitItem>
            {doc.content_warnings && doc.content_warnings.length > 0 && (
              <SplitItem><Label isCompact color="yellow">warnings</Label></SplitItem>
            )}
            <SplitItem>
              <Button variant="plain" size="sm" onClick={() => onDelete(doc.id)}>
                <TimesIcon />
              </Button>
            </SplitItem>
          </Split>
        ))}
      </CardBody>
    </Card>
  );
}
