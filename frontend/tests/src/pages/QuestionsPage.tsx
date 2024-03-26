import React, {useEffect, useRef, useState} from 'react'
import {useMutation, useQuery} from 'react-query'
import {useLocation} from 'react-router-dom'
import axios from "axios";
import {Prueba, RespuestaParams} from "../interfaces";
import {getCsrfToken} from "../csrf";
import {Button} from "@chakra-ui/react";

const fetchPrueba = async (codigo: string): Promise<Prueba> => {
    const resp = await axios.get(`/api/tests/tests/?codigo=${codigo}`)
    if (resp.status !== 200) {
        throw new Error(`Error al obtener las preguntas: ${resp.data}`)
    }
    return resp.data
}

// Simula el envío de una respuesta a un endpoint
const submitRespuesta = async ({codigo, idPregunta, respuesta}: RespuestaParams): Promise<void> => {
    const result = await axios.post(
        `/api/tests/respuestas_likert_noas/?codigo=${codigo}`,
        {
            pregunta: idPregunta,
            alternativa: respuesta,
        },
        {
            headers: {
                'X-CSRFToken': getCsrfToken(),
            }
        }
    )
    if (result.status !== 201) {
        throw new Error(`Error al enviar la respuesta: ${result.data}`)
    }
}

// Hook personalizado para manejar los query params
function useQueryParams() {
    return new URLSearchParams(useLocation().search)
}

const QuestionsPage: React.FC = () => {
    const queryParams = useQueryParams()
    const codigo = queryParams.get('codigo') || ''
    const [autoScroll, setAutoScroll] = useState(true)
    const [respuestas, setRespuestas] = useState<{ [preguntaId: number]: string }>({})
    const preguntaRefs = useRef<(HTMLDivElement | null)[]>([])

    const {data: prueba, isLoading, error} = useQuery(['fetchPrueba', codigo], () => fetchPrueba(codigo))
    const mutation = useMutation(({codigo, idPregunta, respuesta}: RespuestaParams) => submitRespuesta({
        codigo,
        idPregunta,
        respuesta
    }))

    const preguntas = prueba?.preguntalikertnoas_set

    const handleAnswerSelect = (idPregunta: number, respuesta: string) => {
        // Actualizar el estado de respuestas
        const nuevasRespuestas = {...respuestas, [idPregunta]: respuesta}
        setRespuestas(nuevasRespuestas)

        mutation.mutate({codigo, idPregunta, respuesta})

        if (autoScroll) {
            // Encontrar la siguiente pregunta sin respuesta
            const siguientePreguntaSinResponder = prueba?.preguntalikertnoas_set.find(
                pregunta => !nuevasRespuestas[pregunta.id]
            )
            if (siguientePreguntaSinResponder) {
                const index = prueba!.preguntalikertnoas_set.findIndex(p => p.id === siguientePreguntaSinResponder.id)
                preguntaRefs.current[index]?.scrollIntoView({behavior: 'smooth'})
            }
        }
    }

    useEffect(() => {
        // Siempre apuntar a la primera pregunta al cargar
        if (preguntaRefs.current.length > 0 && preguntaRefs.current[0]) {
            preguntaRefs.current[0].scrollIntoView({behavior: 'smooth'})
        }
    }, [preguntas?.length])

    return (
        <div style={{padding: "20px"}}>
            <div style={{position: "fixed", bottom: "20px", right: "20px", zIndex: 1000}}>
                <label>
                    Auto-scroll
                    <input
                        type="checkbox"
                        checked={autoScroll}
                        onChange={() => setAutoScroll(!autoScroll)}
                    />
                </label>
            </div>
            {isLoading ? (
                <div>Cargando...</div>
            ) : error ? (
                <div>Ocurrió un error al cargar las preguntas</div>
            ) : (
                prueba?.preguntalikertnoas_set.map((pregunta, index) => (
                    <div key={pregunta.id} ref={el => preguntaRefs.current[index] = el} style={{marginBottom: "20px"}}>
                        <p>{pregunta.texto}</p>
                        {["Nunca", "Ocasionalmente", "A menudo", "Siempre"].map(respuesta => (
                            <Button
                                key={respuesta}
                                colorScheme={respuestas[pregunta.id] === respuesta[0] ? "blue" : "gray"}
                                variant={respuestas[pregunta.id] === respuesta[0] ? "solid" : "outline"}
                                onClick={() => handleAnswerSelect(pregunta.id, respuesta[0])}
                            >
                                {respuesta}
                            </Button>
                        ))}
                    </div>
                ))
            )}
        </div>
    )
}

export default QuestionsPage
