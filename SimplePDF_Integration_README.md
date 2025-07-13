# SimplePDF Integration

This document explains the SimplePDF integration that has been added to the React autofill form application.

## Overview

SimplePDF is a powerful PDF editor that allows users to view, edit, sign, and annotate PDF documents directly in the browser. The integration provides seamless PDF editing capabilities within your React application.

## Features Implemented

### 1. PDF Viewing
- **View Button**: Click the blue eye icon next to any completed PDF document
- **Full-screen Modal**: PDFs open in a responsive modal with SimplePDF viewer
- **Native PDF Controls**: Zoom, navigate, and interact with PDF content

### 2. PDF Editing
- **Edit Button**: Click the green edit icon next to any PDF document
- **SimplePDF Editor**: Full editing capabilities including:
  - Text editing and annotations
  - Digital signatures
  - Form filling
  - Drawing and highlighting tools
  - Page management

### 3. Document Management
- **Download Original**: Direct download link for the original PDF
- **Auto-detection**: Automatically detects PDF vs non-PDF documents
- **Error Handling**: Graceful handling of loading errors and non-PDF files

## Technical Implementation

### Components Added

1. **PDFViewer Component** (`frontend/src/components/PDFViewer.tsx`)
   - Modal-based PDF viewer/editor
   - Integrates with SimplePDF embed URLs
   - Handles both view and edit modes
   - Supports fallback for non-PDF documents

2. **Backend Download Endpoint** (`backend/main.py`)
   - New endpoint: `GET /api/documents/{doc_id}/download`
   - Secure document access with user authentication
   - Proper MIME type handling

### Integration Details

#### SimplePDF URLs
- **Viewer**: `https://embed.simplepdf.eu/viewer?open={encoded_document_url}`
- **Editor**: `https://embed.simplepdf.eu/editor?open={encoded_document_url}`

#### Authentication
- Documents are served through authenticated endpoints
- User permissions are verified before serving files
- Secure token-based access to prevent unauthorized downloads

## Usage Instructions

### For End Users

1. **Upload a PDF Document**
   - Use the file upload interface to upload a PDF
   - Wait for processing to complete (status shows "Ready to use")

2. **View a PDF**
   - Click the blue eye icon next to any completed PDF document
   - The PDF will open in a full-screen viewer
   - Use SimplePDF's native controls to navigate and interact

3. **Edit a PDF**
   - Click the green edit icon next to any PDF document
   - The PDF will open in SimplePDF's editor
   - Add signatures, annotations, text, and more
   - Changes are made in the SimplePDF interface

4. **Download Original**
   - Click "Download Original" in the PDF viewer footer
   - Downloads the original uploaded PDF file

### For Developers

#### Adding View/Edit Buttons
```tsx
{document.processing_status === 'completed' && (
  <>
    <button onClick={() => handleViewDocument(doc)}>
      <Eye className="w-4 h-4" />
    </button>
    {doc.type === 'application/pdf' && (
      <button onClick={() => handleEditDocument(doc)}>
        <Edit className="w-4 h-4" />
      </button>
    )}
  </>
)}
```

#### Using the PDFViewer Component
```tsx
<PDFViewer
  isOpen={pdfViewerOpen}
  onClose={handleClosePdfViewer}
  document={selectedDocument}
  mode={pdfViewerMode} // 'view' or 'edit'
/>
```

## Dependencies

- **@simplepdf/react-embed-pdf**: React component for SimplePDF integration
- **lucide-react**: Icons for UI elements
- **Backend**: FastAPI with file serving capabilities

## Configuration

### Environment Variables
```bash
# Frontend
REACT_APP_API_URL=https://your-backend-url.com

# Backend (existing)
# No additional configuration needed for SimplePDF
```

### SimplePDF Service
- Uses the free SimplePDF embed service
- No API keys required for basic functionality
- For advanced features, consider SimplePDF Pro

## Security Considerations

1. **Document Access Control**
   - All documents are served through authenticated endpoints
   - User ownership is verified before serving files
   - Document URLs are temporary and secured

2. **CORS Configuration**
   - Backend allows SimplePDF domains for iframe embedding
   - Proper CORS headers for cross-origin requests

3. **File Validation**
   - Document types are validated before serving
   - File existence is verified before creating SimplePDF URLs

## Troubleshooting

### Common Issues

1. **PDF Not Loading**
   - Check if the document exists and is accessible
   - Verify user authentication
   - Check browser console for CORS errors

2. **Edit Mode Not Working**
   - Ensure the document is a valid PDF
   - Check if SimplePDF service is accessible
   - Verify document download URL is working

3. **Iframe Issues**
   - Some browsers may block iframes from external sources
   - Check browser security settings
   - Try in a different browser or incognito mode

### Debug Steps

1. **Check Document URL**
   ```javascript
   // Test the document download URL directly
   const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://autofill-backend-a64u.onrender.com'
   const documentUrl = `${API_BASE_URL}/documents/${doc_id}/download`
   ```

2. **Verify SimplePDF URL**
   ```javascript
   // Check the constructed SimplePDF URL
   const simplePdfUrl = `https://embed.simplepdf.eu/editor?open=${encodeURIComponent(documentUrl)}`
   ```

3. **Test Backend Endpoint**
   ```bash
   curl -H "X-User-ID: your-user-id" \
        -H "Authorization: Bearer your-token" \
        https://your-backend-url.com/api/documents/doc-id/download
   ```

## Future Enhancements

1. **SimplePDF Pro Integration**
   - Custom branding
   - Advanced form features
   - Webhook integration for document changes

2. **Document Version Control**
   - Save edited versions
   - Track document history
   - Merge changes back to original

3. **Collaborative Editing**
   - Real-time collaboration
   - Comment system
   - Review workflows

## Support

For issues related to:
- **SimplePDF functionality**: Visit [SimplePDF Documentation](https://simplepdf.eu/help)
- **Integration issues**: Check the browser console and backend logs
- **Authentication problems**: Verify Supabase configuration and user tokens

---

**Note**: This integration uses SimplePDF's free embed service. For production applications with high volume or advanced features, consider upgrading to SimplePDF Pro. 