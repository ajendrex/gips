import {PreguntaLikertNOAS, RespuestaParams} from "../interfaces"
import React, {useCallback, useEffect, useRef, useState} from "react"
import {useMutation} from "react-query"
import {
    Alert,
    AlertDescription,
    AlertIcon,
    Box,
    Button, calc,
    Card,
    FormControl,
    FormLabel,
    Heading,
    Radio,
    RadioGroup, Spinner,
    Stack,
    Switch,
    Text
} from "@chakra-ui/react"
import axios from "axios"

const submitRespuesta = async ({codigo, idPregunta, respuesta}: RespuestaParams): Promise<void> => {
    await axios.post(
        `/api/tests/respuestas-likert-noas/?codigo=${codigo}`,
        {
            pregunta: idPregunta,
            alternativa: respuesta,
        },
        {
            timeout: 5000,
        }
    )
}

const findNextQuestion = (
        preguntas: PreguntaLikertNOAS[],
        respuestas: { [preguntaId: number]: string },
        currentId: number,
    ): number => {
    // un booleano para saber si ya pasamos la pregunta actual
    let pastCurrent = false
    let index = 0
    // un índice para la primera pregunta sin responder
    let firstUnanswered = -1
    // un índice para la siguiente pregunta sin responder
    let nextUnanswered = -1

    for (const pregunta of preguntas) {
        if (!respuestas[pregunta.id]) {
            if (firstUnanswered === -1) {
                firstUnanswered = index
            }
            if (pastCurrent) {
                nextUnanswered = index
                break
            }
        }
        if (pregunta.id === currentId) {
            pastCurrent = true
        }

        index++
    }

    // si no hay preguntas sin responder, devolvemos -1; lo que se usa para hacer scroll al final
    return nextUnanswered !== -1 ? nextUnanswered : firstUnanswered
}

interface PreguntasProps {
    preguntas: PreguntaLikertNOAS[]
    codigo: string
    successCallback: () => void
    terminar: () => void
    error: string | null
    parentHeight: number
    parentHeightTop: number
}

export const Preguntas = ({preguntas, codigo, successCallback, terminar, error, parentHeight, parentHeightTop}: PreguntasProps) => {
    const [autoScroll, setAutoScroll] = useState(true)
    const [respuestas, setRespuestas] = useState<{ [preguntaId: number]: string }>({})
    const preguntaRefs = useRef<(HTMLDivElement | null)[]>([])
    const [preguntaEnFoco, setPreguntaEnFoco] = useState<number | null>(null)
    const [preguntaRespondida, setPreguntaRespondida] = useState<number | null>(null)
    const [respuestasPendientes, setRespuestasPendientes] = useState<number[]>([])
    const [respuestasConError, setRespuestasConError] = useState<number[]>([])
    const [reintentando, setReintentando] = useState(false)

    const space = 100
    const paddingBottom = 100
    const bottomBoxHeight = 700

    const heightNotFromQuestions = parentHeight + paddingBottom + space + bottomBoxHeight
    const heightBeforeQuestions = parentHeightTop + space

    const removeFromPendientes = (id: number) => (prev: number[]) => {
        const newPendientes = prev.filter(i => i !== id)
        if (!newPendientes.length) {
            setReintentando(false)
        }
        return newPendientes
    }

    const mutation = useMutation(
        ({codigo, idPregunta, respuesta}: RespuestaParams) => submitRespuesta({
            codigo,
            idPregunta,
            respuesta
        }),
        {
            onSuccess: async (data, variables) => {
                setRespuestasPendientes(removeFromPendientes(variables.idPregunta))
                setRespuestasConError(prev => (prev.filter(id => id !== variables.idPregunta)))
            },
            onError: async (error, variables) => {
                console.log('Error guardando respuesta para pregunta', variables.idPregunta)
                setRespuestasConError(prev => ([...prev, variables.idPregunta]))
                setRespuestasPendientes(removeFromPendientes(variables.idPregunta))
            },
            retry: 3,
            retryDelay: 1000,
        }
    )

    const reintentarGuardarRespuestas = () => {
        const respuestasAReintentar = Array.from(new Set(respuestasConError))
        if (respuestasAReintentar.length) {
            setReintentando(true)
            for (const idPregunta of respuestasAReintentar) {
                setRespuestasPendientes(prev => ([...prev, idPregunta]))
                mutation.mutate({codigo, idPregunta, respuesta: respuestas[idPregunta]})
            }
        }
    }

    useEffect(() => {
        if (preguntaRefs.current[0]) {
            setPreguntaEnFoco(preguntas[0].id)
        }
    }, [preguntas, preguntaRefs])

    const calcularAlturas = useCallback(() => {
            const alturaTotalDocumento = document.documentElement.scrollHeight
            const alturaViewport = window.innerHeight
            const maxScrollY = alturaTotalDocumento - alturaViewport
            const alturaPorPregunta = (alturaTotalDocumento - heightNotFromQuestions) / (preguntas.length || 1)
            const scrollPregunta = Math.max(window.scrollY - heightBeforeQuestions + alturaPorPregunta * 0.9, 0)
            const indicePreguntaEnFoco = Math.floor(scrollPregunta / alturaPorPregunta)

            console.debug(
                `h_total: ${alturaTotalDocumento}, viewPort: ${alturaViewport}, alturaPorPregunta: ${alturaPorPregunta}, ` +
                `maxScrolY: ${maxScrollY} scrollY: ${window.scrollY}, indicePregunta: ${indicePreguntaEnFoco}`
            )

            return {alturaTotalDocumento, alturaViewport, maxScrollY, alturaPorPregunta, indicePreguntaEnFoco}
        },
        [preguntas, heightNotFromQuestions, heightBeforeQuestions]
    )

    useEffect(() => {
        const observarScroll = () => {
            const {indicePreguntaEnFoco} = calcularAlturas()
            // Asegura que el índice está dentro de los límites del array de preguntas
            if (indicePreguntaEnFoco >= 0 && indicePreguntaEnFoco < (preguntas.length || 0)) {
                const preguntaId = preguntas[indicePreguntaEnFoco].id
                setPreguntaEnFoco(preguntaId || null)
            }
        }

        window.addEventListener('scroll', observarScroll)

        return () => {
            window.removeEventListener('scroll', observarScroll)
        }
    }, [preguntas, calcularAlturas])

    const handleAnswerSelect = (idPregunta: number, respuesta: string) => {
        setPreguntaRespondida(idPregunta)
        setRespuestas(prev => ({...prev, [idPregunta]: respuesta}))

        setRespuestasPendientes(prev => ([...prev, idPregunta]))
        mutation.mutate({codigo, idPregunta, respuesta})
    }

    const enfocarPregunta = useCallback((index: number) => {
            const {maxScrollY, alturaPorPregunta} = calcularAlturas()

            if (index === -1) {
                window.scrollTo({top: maxScrollY - paddingBottom - 60, behavior: 'smooth'})
            } else if (autoScroll) {
                // Calcula el nuevo scrollY basado en el índice de la pregunta
                const nuevoScrollY = index * alturaPorPregunta

                // Mueve el scroll a la posición calculada
                window.scrollTo({top: nuevoScrollY, behavior: 'smooth'})
            } else if (index < preguntaRefs.current.length) {
                setPreguntaEnFoco(preguntas[index].id)
            }
        },
        [preguntas, autoScroll, calcularAlturas]
    )

    useEffect(() => {
        if (autoScroll && preguntaRespondida !== null) {
            const siguientePreguntaIndex = findNextQuestion(preguntas, respuestas, preguntaRespondida);
            enfocarPregunta(siguientePreguntaIndex);
        }
    }, [respuestas, autoScroll, preguntaRespondida, preguntas, enfocarPregunta]);

    return (
        <Box paddingBottom={`${paddingBottom}px`}>
            <Box position="fixed" top="20px" right="20px" zIndex="1000">
                <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="auto-scroll" mb="0" mr="2">
                        Auto-scroll
                    </FormLabel>
                    <Switch id="auto-scroll" isChecked={autoScroll} onChange={() => setAutoScroll(!autoScroll)} />
                </FormControl>
            </Box>
            <Box h={`${space}px`} />
            {
                preguntas.map((pregunta, index) => (
                    <Box
                        key={pregunta.id}
                        ref={el => preguntaRefs.current[index] = el}
                        padding="20px"
                        mb="4"
                        boxShadow="lg"
                        borderRadius="md"
                        opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                        onClick={() => enfocarPregunta(index)}
                    >
                        <Box
                            h={150}
                            display="flex"
                            flexDirection="column"
                            justifyContent="center"
                        >
                            <Text
                                align="center"
                                fontWeight="bold"
                                fontFamily="'Roboto Slab', serif"
                                opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                            >{pregunta.texto}</Text>
                        </Box>
                        <Box
                            display="flex"
                            flexDirection="row"
                            alignItems="center"
                            justifyContent="space-between"
                        >
                            <RadioGroup
                                onChange={(value) => handleAnswerSelect(pregunta.id, value)}
                                value={respuestas[pregunta.id]}
                            >
                                <Stack direction="column">
                                    {[
                                        {text: "Rara vez o nunca", code: "N"},
                                        {text: "Ocasionalmente", code: "O"},
                                        {text: "A menudo", code: "A"},
                                        {text: "Siempre o casi siempre", code: "S"},
                                    ].map(({text, code}) => (
                                        <Radio
                                            key={code}
                                            value={code}
                                            opacity={preguntaEnFoco === pregunta.id ? 1 : 0.5}
                                            isDisabled={reintentando || respuestasPendientes.includes(pregunta.id)}
                                        >
                                            {text}
                                        </Radio>
                                    ))}
                                </Stack>
                            </RadioGroup>
                            {!reintentando && respuestasPendientes.includes(pregunta.id) ? (
                                <Spinner />
                            ) : null}
                        </Box>
                    </Box>
                ))
            }
            <Box h={`${bottomBoxHeight}px`}>
                {
                    Object.keys(respuestas).length === preguntas.length ? (
                        respuestasPendientes.length ? (
                            <Spinner />
                        ) : respuestasConError.length || reintentando ? (
                            <Stack spacing="30px" align="center">
                                <Alert status="error">
                                    <AlertIcon />
                                    <AlertDescription>
                                        Hubo problemas guardando algunas respuestas. Asegúrate de tener internet y luego
                                        pincha el botón reintentar.
                                    </AlertDescription>
                                </Alert>
                                { reintentando ? (
                                    <Spinner />
                                ) : (
                                    <Button
                                        width="50%"
                                        onClick={reintentarGuardarRespuestas}
                                        variant="solid"
                                        colorScheme="green"
                                    >
                                        Reintentar
                                    </Button>
                                )}
                            </Stack>
                        ) : (
                            <Card p="10px">
                                <Box
                                    display="flex"
                                    justifyContent="center"
                                    alignItems="center"
                                    flexDirection="column"
                                >
                                    <Stack spacing="30px">
                                        <Heading size="sm" mt="40px" textAlign="center">
                                            ¡Felicidades!<br />
                                        </Heading>
                                        <Heading size="xs" mt="5px">
                                            ¡Has completado la primera etapa de tu evaluación psicológica sobre el control de los impulsos!
                                        </Heading>
                                        <Text lineHeight="25px">
                                            Ahora solo falta un paso más para finalizar tu evaluación: agendar una entrevista
                                            psicológica por videollamada con uno de nuestros profesionales.
                                        </Text>
                                        <Text lineHeight="25px">
                                            No te preocupes, el día que elijas un psicólogo de nuestro equipo se pondrá en
                                            contacto contigo a través de WhatsApp antes de la entrevista para explicarte
                                            y coordinar todos los detalles.
                                        </Text>
                                        <Text lineHeight="25px">
                                            ¡Haz clic en el botón "Agendar Entrevista" para programar tu cita!
                                        </Text>
                                        <Box display="flex" justifyContent="center" mb="10px">
                                            <Stack spacing="10px">
                                                <Button
                                                    colorScheme="teal"
                                                    onClick={successCallback}
                                                >
                                                    Agendar Entrevista
                                                </Button>
                                                <Button
                                                    colorScheme="gray"
                                                    onClick={terminar}
                                                >
                                                    Cancelar Evaluación
                                                </Button>
                                            </Stack>
                                        </Box>
                                        {error ? (
                                            <Alert status="error">
                                                <AlertIcon />
                                                <AlertDescription>{error}</AlertDescription>
                                            </Alert>
                                        ) : null}
                                    </Stack>
                                </Box>
                            </Card>
                    )) : null
                }
            </Box>
        </Box>
    )
}
