import React, { useEffect, useState } from 'react'
import '../App.css';

export default function EndpointAudit(props) {
    const [isLoaded, setIsLoaded] = useState(false);
    const [log, setLog] = useState(null);
    const [error, setError] = useState(null)

    // Lab 9 - Add a state for the index
    const [index, setIndex] = useState(null);


    const rand_val = Math.floor(Math.random() * 100); // Get a random event from the event store

    const getAudit = () => {
        fetch(`http://acit3855lab6.eastus.cloudapp.azure.com:8110/${props.endpoint}?index=${rand_val}`)
            .then(res => res.json())
            .then((result) => {
                console.log("Received Audit Results for " + props.endpoint)
                setLog(result);

                // Lab 9 - Set the index upon successfully response from the audit endpoints
                setIndex(rand_val);
                setIsLoaded(true);
            }, (error) => {
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
        const interval = setInterval(() => getAudit(), 4000); // Update every 4 seconds
        return () => clearInterval(interval);
    }, [getAudit]);

    if (error) {
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false) {
        return (<div>Loading...</div>)
    } else if (isLoaded === true) {

        return (
            <div>
                <h3>{props.endpoint}-{index}</h3>
                {JSON.stringify(log)}
            </div>
        )
    }
}
