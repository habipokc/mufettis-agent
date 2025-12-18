import { NextRequest, NextResponse } from 'next/server';

// Backend URL - Docker internal network
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();

        // Get Authorization header from client request
        const authHeader = request.headers.get('Authorization');

        // Build headers for backend request
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };

        if (authHeader) {
            headers['Authorization'] = authHeader;
        }

        // Proxy request to backend
        const backendResponse = await fetch(`${BACKEND_URL}/api/v1/search/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(body),
        });

        // Handle error responses
        if (!backendResponse.ok) {
            const errorData = await backendResponse.json().catch(() => ({}));
            return NextResponse.json(
                { detail: errorData.detail || 'Backend error' },
                { status: backendResponse.status }
            );
        }

        // Return successful response
        const data = await backendResponse.json();
        return NextResponse.json(data);

    } catch (error: any) {
        console.error('API Proxy Error:', error);
        return NextResponse.json(
            { detail: error.message || 'Internal server error' },
            { status: 500 }
        );
    }
}
