import { useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, Clock, MapPin, Camera, Mic, Upload, Loader2, X, Eye } from 'lucide-react';
import { apiFetch } from '../../lib/api';
import type { ReportReceipt } from '../../lib/types';

interface MediaUploadURLResponse {
  upload_url: string;
  s3_key: string;
  expires_in: number;
  media_asset_id: string;
}

export function ReportReceiptPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const voiceInputRef = useRef<HTMLInputElement>(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [uploadingVoice, setUploadingVoice] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const { data: receipt, isLoading, error } = useQuery({
    queryKey: ['report-receipt', id],
    queryFn: () => apiFetch<ReportReceipt>(`/api/v1/reports/${id}/receipt`),
    enabled: !!id,
    refetchInterval: 5000,
  });

  // Step 1: Request presigned upload URL
  const uploadUrlMutation = useMutation({
    mutationFn: async ({ mimeType, fileSize, mediaType }: { mimeType: string; fileSize: number; mediaType: string }) => {
      const endpoint = mediaType === 'voice' ? 'voice-upload-url' : 'media-upload-url';
      return apiFetch<MediaUploadURLResponse>(`/api/v1/reports/${id}/${endpoint}`, {
        method: 'POST',
        body: JSON.stringify({ mime_type: mimeType, file_size: fileSize, media_type: mediaType }),
      });
    },
  });

  // Step 2: Confirm upload and enqueue analysis
  const confirmUploadMutation = useMutation({
    mutationFn: async ({ s3Key, sha256, mimeType, fileSize, mediaType }: { s3Key: string; sha256: string; mimeType: string; fileSize: number; mediaType: string }) => {
      return apiFetch<{
        media_asset_id: string;
        processing_status: string;
        analysis_enqueued: boolean;
        analysis_status: string | null;
        analysis_provider: string | null;
        analysis_error: string | null;
        is_demo_analysis: boolean;
      }>(`/api/v1/reports/${id}/media-complete`, {
        method: 'POST',
        body: JSON.stringify({ s3_key: s3Key, sha256, mime_type: mimeType, file_size: fileSize, media_type: mediaType }),
      });
    },
  });

  async function computeSHA256(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
  }

  async function handleFileUpload(file: File, mediaType: 'photo' | 'voice') {
    if (!id) return;
    setUploadError(null);
    setUploadSuccess(null);
    const setUploading = mediaType === 'voice' ? setUploadingVoice : setUploadingPhoto;

    try {
      setUploading(true);

      // Step 1: Request presigned URL
      const uploadData = await uploadUrlMutation.mutateAsync({
        mimeType: file.type,
        fileSize: file.size,
        mediaType,
      });

      // Step 2: Upload file directly to S3 (or local storage)
      const uploadResponse = await fetch(uploadData.upload_url, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type },
      });

      if (!uploadResponse.ok && uploadData.upload_url.startsWith('file://')) {
        // Local dev fallback — file:// URLs can't be fetched, skip the actual upload
        // The backend local storage handler will accept the confirmation
      } else if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }

      // Step 3: Compute SHA-256 and confirm upload
      const sha256 = await computeSHA256(file);
      const confirmResult = await confirmUploadMutation.mutateAsync({
        s3Key: uploadData.s3_key,
        sha256,
        mimeType: file.type,
        fileSize: file.size,
        mediaType,
      });

      // Build success message based on analysis result
      if (mediaType === 'voice') {
        setUploadSuccess('Voice note uploaded. Use the transcribe option to convert to text.');
      } else if (confirmResult.analysis_error) {
        setUploadSuccess(`Photo uploaded, but AI analysis failed: ${confirmResult.analysis_error}`);
      } else if (confirmResult.analysis_status === 'completed') {
        const providerLabel = confirmResult.is_demo_analysis ? 'Demo analysis' : `AI analysis (${confirmResult.analysis_provider || 'provider'})`;
        setUploadSuccess(`Photo uploaded and analyzed. ${providerLabel} completed successfully.`);
      } else if (confirmResult.analysis_status === 'processing') {
        setUploadSuccess('Photo uploaded. AI analysis is processing...');
      } else if (confirmResult.analysis_enqueued) {
        setUploadSuccess('Photo uploaded. AI analysis has been enqueued.');
      } else {
        setUploadSuccess('Photo uploaded successfully.');
      }

      queryClient.invalidateQueries({ queryKey: ['report-receipt', id] });
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  function onPhotoSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file, 'photo');
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function onVoiceSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file, 'voice');
    if (voiceInputRef.current) voiceInputRef.current.value = '';
  }

  if (isLoading) {
    return <div className="mx-auto max-w-lg px-4 py-8 text-slate-500">Loading receipt...</div>;
  }

  if (error || !receipt) {
    return (
      <div className="mx-auto max-w-lg px-4 py-8">
        <p className="text-red-500">Could not load receipt.</p>
        <Link to="/report" className="btn-secondary mt-4">Back to Report Form</Link>
      </div>
    );
  }

  const statusSteps = ['submitted', 'under_review', 'verified'];
  const currentStep = statusSteps.indexOf(receipt.status);

  return (
    <div className="mx-auto max-w-lg px-4 py-8">
      {/* Success header */}
      <div className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-50">
          <CheckCircle2 className="h-8 w-8 text-green-500" />
        </div>
        <h1 className="mt-3 text-xl font-bold text-slate-900">Report Submitted</h1>
        <p className="mt-1 text-sm text-slate-600">
          Your report has been received. Save this receipt to check status.
        </p>
      </div>

      {/* Receipt details */}
      <div className="card mt-6 p-5">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-slate-600">Report ID</dt>
            <dd className="font-mono text-xs">{receipt.id}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Type</dt>
            <dd>{receipt.report_type}</dd>
          </div>
          {receipt.hazard_type && (
            <div className="flex justify-between">
              <dt className="text-slate-600">Hazard</dt>
              <dd>{receipt.hazard_type}</dd>
            </div>
          )}
          <div className="flex justify-between">
            <dt className="text-slate-600">Location</dt>
            <dd>
              <MapPin className="inline h-3.5 w-3.5 text-slate-400" />
              {' '}{receipt.latitude_coarse.toFixed(2)}, {receipt.longitude_coarse.toFixed(2)} (approx.)
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Submitted</dt>
            <dd>{new Date(receipt.submitted_at).toLocaleString('en-GB')}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-600">Media</dt>
            <dd>{receipt.media_count} item(s)</dd>
          </div>
          {receipt.is_synthetic && (
            <p className="text-xs text-amber-600">This is a synthetic demo report.</p>
          )}
        </dl>
      </div>

      {/* Status tracker */}
      <div className="mt-4 card p-5">
        <h2 className="text-sm font-medium text-slate-700">Status</h2>
        <ol className="mt-3 space-y-3">
          {statusSteps.map((step, i) => {
            const isDone = i <= currentStep;
            const isCurrent = i === currentStep;
            return (
              <li key={step} className="flex items-center gap-3">
                {isDone ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : (
                  <Clock className="h-5 w-5 text-slate-300" />
                )}
                <span className={isCurrent ? 'font-medium text-slate-900' : 'text-slate-400'}>
                  {step.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
              </li>
            );
          })}
        </ol>
        {receipt.ai_analysis_status && (
          <p className="mt-3 text-xs text-slate-500">
            AI Analysis: {receipt.ai_analysis_status}
          </p>
        )}
      </div>

      {/* Photo upload */}
      <div className="mt-4 card p-5">
        <h2 className="text-sm font-medium text-slate-900">Add Photo</h2>
        <p className="mt-1 text-xs text-slate-500">
          Upload photos of the flooding or drainage issue. Photos are analyzed by AI to identify visible hazards.
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={onPhotoSelected}
          aria-label="Upload photo"
        />
        <button
          className="btn-primary mt-3 w-full"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadingPhoto}
        >
          {uploadingPhoto ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading...
            </>
            ) : (
              <>
                <Camera className="h-4 w-4" />
                Upload Photo
              </>
            )}
        </button>
        <p className="mt-2 text-xs text-slate-400">JPG, PNG, or WebP. Max 20MB.</p>
      </div>

      {/* Voice note upload */}
      <div className="mt-4 card p-5">
        <h2 className="text-sm font-medium text-slate-900">Add Voice Note</h2>
        <p className="mt-1 text-xs text-slate-500">
          Upload a short voice description. It will be transcribed to text and shown for your review.
        </p>
        <input
          ref={voiceInputRef}
          type="file"
          accept="audio/webm,audio/mp4,audio/mpeg,audio/wav,audio/ogg"
          className="hidden"
          onChange={onVoiceSelected}
          aria-label="Upload voice note"
        />
        <button
          className="btn-secondary mt-3 w-full"
          onClick={() => voiceInputRef.current?.click()}
          disabled={uploadingVoice}
        >
          {uploadingVoice ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Uploading...
            </>
            ) : (
              <>
                <Mic className="h-4 w-4" />
                Upload Voice Note
              </>
            )}
        </button>
        <p className="mt-2 text-xs text-slate-400">WebM, MP3, WAV, or OGG. Max 25MB.</p>
      </div>

      {/* Upload status messages */}
      {uploadError && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <X className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{uploadError}</span>
        </div>
      )}
      {uploadSuccess && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
          <span>{uploadSuccess}</span>
        </div>
      )}

      {/* Navigation */}
      <div className="mt-4 flex gap-3">
        <Link to={`/reports/${id}`} className="btn-primary">
          <Eye className="h-4 w-4" />
          View Full Details
        </Link>
        <Link to="/report" className="btn-secondary">
          <Upload className="h-4 w-4" />
          New Report
        </Link>
        <Link to="/map" className="btn-secondary">
          View Map
        </Link>
      </div>
    </div>
  );
}
