import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

    const getStats = () => {
        fetch(`http://acit3855lab6.eastus.cloudapp.azure.com/processing/stats`)
            .then(res => res.json())
            .then(
                (result) => {
                    console.log("Received Stats")
                    setStats(result);
                    setIsLoaded(true);
                },
                (error) => {
                    setError(error)
                    setIsLoaded(true);
                })
    }

    useEffect(() => {
        const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
        return () => clearInterval(interval);
    }, [getStats]);



    if (error) {
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (!isLoaded) {
        return (<div>Loading...</div>)
    } else {
        return (
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
                    <tbody>
                        <tr>
                            <th>Create Posts</th>
                            <th>Follow Events</th>
                            <th>Total Likes</th>
                            <th>Total Follow Count</th>
                        </tr>
                        <tr>
                            <td># Posts: {stats['num_create_posts']}</td>
                            <td># Events: {stats['num_follow_events']}</td>
                            <td># Likes: {stats['total_likes']}</td>
                            <td># Follows: {stats['total_follow_count']}</td>
                        </tr>
                    </tbody>
                </table>
                <h3>Last Updated: {stats['last_updated']}</h3>
            </div>
        )
    }
}
