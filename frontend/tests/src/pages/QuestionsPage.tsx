import React, {useEffect, useRef, useState} from 'react'
import {useMutation, useQuery} from 'react-query'
import {useLocation} from 'react-router-dom'
import axios from "axios"
import {Prueba, RespuestaParams} from "../interfaces"
import {getCsrfToken} from "../csrf"
import {Box, Button, FormControl, FormLabel, Radio, RadioGroup, Stack, Switch, Text} from "@chakra-ui/react"

const fetchPrueba = async (codigo: string): Promise<Prueba> => {
    const resp = await axios.get(`/api/tests/tests/?codigo=${codigo}`)
    if (resp.status !== 200) {
        throw new Error(`Error al obtener las preguntas: ${resp.data}`)
    }
    return resp.data
}

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
        <div style={{display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", padding: "20px"}}>
            <Box width="100%" maxW="500px">
                <Box position="fixed" bottom="20px" right="20px" zIndex="1000">
                    <FormControl display="flex" alignItems="center">
                        <FormLabel htmlFor="auto-scroll" mb="0" mr="2">
                            Auto-scroll
                        </FormLabel>
                        <Switch id="auto-scroll" isChecked={autoScroll} onChange={() => setAutoScroll(!autoScroll)} />
                    </FormControl>
                </Box>
                {isLoading ? (
                    <div>Cargando...</div>
                ) : error ? (
                    <div>Ocurrió un error al cargar las preguntas</div>
                ) : (
                    <>
                    {
                        prueba?.preguntalikertnoas_set.map((pregunta, index) => (
                            <Box
                                key={pregunta.id}
                                ref={el => preguntaRefs.current[index] = el}
                                padding="20px"
                                mb="4"
                                boxShadow="lg"
                                borderRadius="md"
                            >
                                <Box h={150} display="flex" flexDirection="column" justifyContent="center">
                                    <Text align="center" fontWeight="bold" fontFamily="'Roboto Slab', serif">{pregunta.texto}</Text>
                                </Box>
                                <RadioGroup onChange={(value) => handleAnswerSelect(pregunta.id, value)} value={respuestas[pregunta.id]}>
                                    <Stack direction="column">
                                        {[
                                            {text: "Rara vez o nunca", code: "N"},
                                            {text: "Ocasionalmente", code: "O"},
                                            {text: "A menudo", code: "A"},
                                            {text: "Siempre o casi siempre", code: "S"},
                                        ].map(({text, code}) => (
                                            <Radio key={code} value={code}>
                                                {text}
                                            </Radio>
                                        ))}
                                    </Stack>
                                </RadioGroup>
                            </Box>
                        ))
                    }
                    {
                        Object.keys(respuestas).length === prueba?.preguntalikertnoas_set.length && (
                            <div>
                                <p>¡Felicidades! Has completado todas las preguntas.</p>
                                <Button colorScheme="teal" onClick={() => {/* Ir a la siguiente página */}}>
                                    Agendar Llamada
                                </Button>
                            </div>
                        )
                    }
                    </>
                )}
            </Box>
        </div>
    )
}

export default QuestionsPage
