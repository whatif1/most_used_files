"use server"
import {revalidatePath} from "next/cache";
import {headers, cookies} from "next/headers";
import {auth} from "../../auth";


// TODO - signUp
export async function signUp(email, password, name, role) {
    try {
        console.log('Starting registration for:', email);

        const result = await auth.api.signUpEmail({
            body: {
                email,
                password,
                name,
                role
            },
            headers: await headers() // Важно для cookies
        });

        console.log('Registration result:', result);

        // Email будет отправлен автоматически если sendOnSignUp: true
        if (result.user) {
            return {
                success: true,
                requiresVerification: !result.user.emailVerified,
                message: "Registration successful! Check your email for verification.",
                data: result
            };
        }

        return {success: false, message: "Registration failed"};
    } catch (error) {
        console.error('Registration error:', error);
        return {
            success: false,
            message: error.message || "Registration failed"
        };
    }
}


// TODO - resendVerificationEmail - функция для повторной отправки письма
export async function resendVerificationEmail(email) {
    try {
        console.log('Resending verification email to:', email);

        // Better Auth API для повторной отправки
        const result = await auth.api.sendVerificationEmail({
            body: {email},
            headers: await headers()
        });

        return {
            success: true,
            message: "Verification email sent successfully"
        };
    } catch (error) {
        console.error('Resend email error:', error);
        return {
            success: false,
            message: error.message || "Failed to send email"
        };
    }
}


// TODO - signIn
export async function signIn(email, password) {
    try {
        let result = await auth.api.signInEmail({
            body: {email, password}
        });

        // Проверяем подтверждение email при входе
        if (result.user && !result.user.emailVerified) {
            return {
                success: false,
                requiresVerification: true,
                message: "Please verify your email before signing in"
            };
        }

        return {success: true, data: result};
    } catch (error) {
        return {success: false, message: error.message};
    }
}


// TODO - signOut
export async function signOut() {
    let result = await auth.api.signOut({headers: await headers()});
    return result;
}


// TODO - getUnprotectedData
export async function getUnprotectedData(endPoint, params = {}) {
    let mainUrl = process.env.NEXT_PUBLIC_API_URL;
    const cookieStore = await cookies();
    const sessionTokenCookie = cookieStore.get('better-auth.session_token');
    const requestHeaders = new Headers();
    // Если токен есть, добавляем его в заголовки
    if (sessionTokenCookie) {
        requestHeaders.set('Cookie', `better-auth.session_token=${sessionTokenCookie.value}`);
    }

    const queryParams = new URLSearchParams();
    for (const key in params) {
        // Добавляем только параметры с реальным значением
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();
    // Собираем полный URL
    const fullUrl = `${mainUrl}${endPoint}${queryString ? `?${queryString}` : ''}`;

    try {
        let response = await fetch(`${fullUrl}`,
            {cache: "no-cache", headers: requestHeaders});
        if (!response.ok) {
            if (response.status === 404) {
                return false;
            } else {
                // Попробуем прочитать тело ошибки для лучшей диагностики
                const errorBody = await response.json().catch(() => ({detail: "Unknown server error"}));
                throw new Error(errorBody.detail || "Ошибка соединения с сервером.");
            }
        }
        return await response.json();
    } catch (error) {
        console.error("Ошибка при получении данных:", error);
        return false;
    }
}


// TODO - getProtectedData
export async function getProtectedData(endPoint, params = {}) {
    let mainUrl = process.env.NEXT_PUBLIC_API_URL;

    // 2. Получаем доступ к хранилищу cookie из входящего запроса
    const cookieStore = await cookies();
    const sessionTokenCookie = cookieStore.get('better-auth.session_token');

    // Если токена нет, то и запрашивать нечего
    if (!sessionTokenCookie) {
        console.error("Server Action: Cookie 'better-auth.session_token' not found.");
        // Возвращаем false или объект с ошибкой, чтобы фронтенд мог это обработать
        return false;
    }

    // 3. Формируем заголовки для исходящего запроса
    const requestHeaders = new Headers();
    // Устанавливаем заголовок 'Cookie', который и будет прочитан FastAPI
    requestHeaders.set('Cookie', `better-auth.session_token=${sessionTokenCookie.value}`);

    const queryParams = new URLSearchParams();
    for (const key in params) {
        // Добавляем только параметры с реальным значением
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();
    // Собираем полный URL
    const fullUrl = `${mainUrl}${endPoint}${queryString ? `?${queryString}` : ''}`;

    try {
        let response = await fetch(`${fullUrl}`,
            {cache: "no-cache", headers: requestHeaders});
        if (!response.ok) {
            if (response.status === 404) {
                return false;
            } else {
                // Попробуем прочитать тело ошибки для лучшей диагностики
                const errorBody = await response.json().catch(() => ({detail: "Unknown server error"}));
                throw new Error(errorBody.detail || "Ошибка соединения с сервером.");
            }
        }
        return await response.json();
    } catch (error) {
        console.error("Ошибка при получении данных:", error);
        return false;
    }
}


// TODO - createUnprotectedJsonData
export async function createUnprotectedJsonData(data, endPoint, params = {}, fullRevalidatePathStr = '') {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;

    const queryParams = new URLSearchParams();
    for (const key in params) {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();
    const fullUrl = `${apiURL}${endPoint}${queryString ? `?${queryString}` : ''}`;

    try {
        const response = await fetch(`${fullUrl}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const errorData = await response.json();
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }
        if (fullRevalidatePathStr) {
            revalidatePath(fullRevalidatePathStr, 'layout');
        }
        return {success: true, message: 'Recipe created successfully!'};
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


// TODO - createUnprotectedFormData
export async function createUnprotectedFormData(formData, endPoint, fullRevalidatePathStr = '') {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;

    const queryParams = new URLSearchParams();
    for (const key in params) {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();
    const fullUrl = `${apiURL}${endPoint}${queryString ? `?${queryString}` : ''}`;
    try {
        const response = await fetch(`${fullUrl}`, {
            method: 'POST',
            body: formData,
            // ВАЖНО: НЕ устанавливайте заголовок 'Content-Type'. Браузер сделает это автоматически с правильным boundary для multipart/form-data.
        });
        if (!response.ok) {
            const errorData = await response.json();
            // Возвращаем объект с ошибкой, чтобы клиент мог ее обработать
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }
        if (fullRevalidatePathStr) {
            revalidatePath(fullRevalidatePathStr, 'layout');
        }
        return {success: true, message: 'Recipe created successfully!'};
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


// TODO - createProtectedJsonData
export async function createProtectedJsonData(data, endPoint, params = {}, fullRevalidatePathStr = '') {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;

    // 1. Получаем доступ к хранилищу cookie
    const cookieStore = await cookies();
    const sessionTokenCookie = cookieStore.get('better-auth.session_token');

    // 2. Проверяем, есть ли токен
    if (!sessionTokenCookie) {
        console.error("Server Action: Cookie 'better-auth.session_token' not found.");
        return {success: false, message: 'Unauthorized'};
    }

    // 3. Формируем заголовки, включая cookie для аутентификации
    const requestHeaders = new Headers();
    requestHeaders.set('Content-Type', 'application/json');
    requestHeaders.set('Cookie', `better-auth.session_token=${sessionTokenCookie.value}`);

    const queryParams = new URLSearchParams();
    for (const key in params) {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();
    const fullUrl = `${apiURL}${endPoint}${queryString ? `?${queryString}` : ''}`;

    try {
        const response = await fetch(`${fullUrl}`, {
            method: 'POST',
            headers: requestHeaders, // Используем сформированные заголовки
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorData = await response.json();
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }

        if (fullRevalidatePathStr) {
            revalidatePath(fullRevalidatePathStr, 'layout');
        }
        return {success: true, message: 'Message created successfully!'}; // Сообщение лучше сделать более релевантным
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


// TODO - createProtectedFormData
export async function createProtectedFormData(formData, endPoint, fullRevalidatePathStr = '') {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;

    // 1. Получаем доступ к хранилищу cookie
    const cookieStore = await cookies();
    const sessionTokenCookie = cookieStore.get('better-auth.session_token');

    // 2. Проверяем, есть ли токен
    if (!sessionTokenCookie) {
        console.error("Server Action: Cookie 'better-auth.session_token' not found.");
        return {success: false, message: 'Unauthorized'};
    }

    // 4. Формируем заголовки только с cookie
    const requestHeaders = new Headers();
    requestHeaders.set('Cookie', `better-auth.session_token=${sessionTokenCookie.value}`);

    // 5. Отправляем запрос
    try {
        const response = await fetch(`${apiURL}/main_api_app/${endPoint}`, {
            method: 'POST',
            headers: requestHeaders, // Передаем заголовки с cookie
            body: formData,
            // ВАЖНО: 'Content-Type' по-прежнему НЕ устанавливаем. Браузер сделает это сам.
        });

        if (!response.ok) {
            const errorData = await response.json();
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }

        if (fullRevalidatePathStr) {
            revalidatePath(fullRevalidatePathStr, 'layout');
        }
        return {success: true, message: 'Recipe created successfully!'};
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


// TODO - updateProtectedJsonData
export async function updateProtectedJsonData(data, endPoint, instanceId, params = {}, fullRevalidatePathStr = '') {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;

    // 1. Получаем cookie для аутентификации
    const cookieStore = await cookies();
    const sessionTokenCookie = cookieStore.get('better-auth.session_token');

    // 2. Проверяем, авторизован ли пользователь
    if (!sessionTokenCookie) {
        return {success: false, message: 'Unauthorized'};
    }

    // 3. Формируем заголовки: указываем тип контента JSON и передаем cookie
    const requestHeaders = new Headers();
    requestHeaders.set('Content-Type', 'application/json'); // <--- Ключевое отличие от FormData
    requestHeaders.set('Cookie', `better-auth.session_token=${sessionTokenCookie.value}`);

    // 4. Формируем query-параметры
    const queryParams = new URLSearchParams();
    for (const key in params) {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();

    // 5. Собираем полный URL, включая ID экземпляра
    // Убедимся, что endPoint заканчивается на / для корректного URL
    const cleanEndPoint = endPoint.endsWith('/') ? endPoint : `${endPoint}/`;
    const fullUrl = `${apiURL}${cleanEndPoint}${instanceId}${queryString ? `?${queryString}` : ''}`;

    try {
        // 6. Отправляем запрос
        const response = await fetch(`${fullUrl}`, {
            method: 'PATCH', // Используем метод PATCH для частичного обновления
            headers: requestHeaders,
            body: JSON.stringify(data)
        });

        // 7. Обрабатываем ответ сервера
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({detail: "Failed to parse error response"}));
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }

        // 8. Сбрасываем кеш, если необходимо
        if (fullRevalidatePathStr) {
            revalidatePath(fullRevalidatePathStr, 'layout');
        }

        return {success: true, message: 'Data updated successfully!'};

    } catch (error) {
        console.error('Error updating JSON data:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


// TODO - updateProtectedFormData
export async function updateProtectedFormData(formData, instance_id, postId, params = {}, fullRevalidatePathStr = '') {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;

    const cookieStore = await cookies();
    const sessionTokenCookie = cookieStore.get('better-auth.session_token');

    if (!sessionTokenCookie) {
        return {success: false, message: 'Unauthorized'};
    }

    const requestHeaders = new Headers();
    requestHeaders.set('Cookie', `better-auth.session_token=${sessionTokenCookie.value}`);

    const queryParams = new URLSearchParams();
    for (const key in params) {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();
    // postId теперь часть пути, а params - query-строка
    const fullUrl = `${apiURL}${instance_id}${postId}${queryString ? `?${queryString}` : ''}`;

    try {
        // Изменяем метод на PUT и добавляем ID поста в URL
        const response = await fetch(`${fullUrl}`, {
            method: 'PUT', // <--- ИЗМЕНЕНО
            headers: requestHeaders,
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }

        if (fullRevalidatePathStr) {
            revalidatePath(fullRevalidatePathStr, 'layout');
        }
        return {success: true, message: 'Post updated successfully!'};
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


// TODO - deleteProtectedData
export async function deleteProtectedData(endPoint, instance_id, params = {}, fullRevalidatePathStr = '') {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;

    const cookieStore = await cookies();
    const sessionTokenCookie = cookieStore.get('better-auth.session_token');

    if (!sessionTokenCookie) {
        return {success: false, message: 'Unauthorized'};
    }

    const requestHeaders = new Headers();
    requestHeaders.set('Cookie', `better-auth.session_token=${sessionTokenCookie.value}`);

    const queryParams = new URLSearchParams();
    for (const key in params) {
        if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
            queryParams.append(key, params[key]);
        }
    }
    const queryString = queryParams.toString();
    // postId теперь часть пути, а params - query-строка
    const fullUrl = `${apiURL}${endPoint}${instance_id}${queryString ? `?${queryString}` : ''}`;

    try {
        // Изменяем метод на PUT и добавляем ID поста в URL
        const response = await fetch(`${fullUrl}`, {
            method: 'DELETE',
            headers: requestHeaders,
            body: JSON.stringify(({"instance_id": instance_id}))
        });

        if (!response.ok) {
            const errorData = await response.json();
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }

        if (fullRevalidatePathStr) {
            revalidatePath(fullRevalidatePathStr, 'layout');
        }
        return {success: true, message: 'Deleted successfully!'};
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}
