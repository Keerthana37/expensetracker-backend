const fetchData2 = async () => {
    try {
        const token = localStorage.getItem('access_token');
        console.log("Using token:", token?.substring(0, 20) + "..."); // Debug token

        if (!token) {
            console.error("No token found");
            return [];
        }

        const response = await fetch(`http://localhost:8000/transactions/${userId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        console.log("Response status:", response.status);
        
        if (!response.ok) {
            const error = await response.json();
            console.error("API error:", error);
            return [];
        }

        const data = await response.json();
        console.log("API response data:", data);
        return data;
    } catch (error) {
        console.error("Fetch error:", error);
        return [];
    }
} 