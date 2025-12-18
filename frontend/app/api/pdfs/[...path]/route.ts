import { NextRequest, NextResponse } from 'next/server';

// Backend URL - Docker internal network
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000';

export async function GET(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    try {
        const { path } = await params;
        const pdfPath = path.join('/');

        // Fetch PDF from backend
        const backendResponse = await fetch(`${BACKEND_URL}/pdfs/${pdfPath}`, {
            method: 'GET',
        });

        if (!backendResponse.ok) {
            return NextResponse.json(
                { error: 'PDF not found' },
                { status: backendResponse.status }
            );
        }

        // Get the PDF content
        const pdfBuffer = await backendResponse.arrayBuffer();

        // Return PDF with correct headers
        return new NextResponse(pdfBuffer, {
            status: 200,
            headers: {
                'Content-Type': 'application/pdf',
                'Content-Disposition': `inline; filename="${encodeURIComponent(path[path.length - 1])}"`,
                'Cache-Control': 'public, max-age=86400', // Cache for 1 day
            },
        });

    } catch (error: any) {
        console.error('PDF Proxy Error:', error);
        return NextResponse.json(
            { error: error.message || 'Internal server error' },
            { status: 500 }
        );
    }
}
