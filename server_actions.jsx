"use server"
import {revalidatePath} from "next/cache";
import {headers} from "next/headers";
import {auth} from "../../auth";


export async function signUp(email, password, name) {
    try {
        console.log('Starting registration for:', email);

        const result = await auth.api.signUpEmail({
            body: {
                email,
                password,
                name
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

// ✅ Функция для повторной отправки письма
export async function resendVerificationEmail(email) {
    try {
        console.log('📮 Resending verification email to:', email);

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


export async function signOut() {
    let result = await auth.api.signOut({headers: await headers()});
    return result;
}


export async function getUnprotectedData() {
    let mainUrl = process.env.NEXT_PUBLIC_API_URL;
    try {
        let response = await fetch(`${mainUrl}/main_api_app/get_all_recipies`,
            {cache: "no-cache"});
        if (!response.ok) {
            if (response.status === 404) {
                return false;
            }
            throw new Error("Ошибка соединения с сервером.");
        }
        let result = await response.json();
        return result;
    } catch (error) {
        console.error("Ошибка при получении данных:", error);
        return false;
    }
}


export async function createUnprotectedFormData(data) {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;
    const formData = new FormData();
    formData.append('instructions', data.instructions);
    // `data.image` - это объект File, который мы получили из InputFileUpload
    if (data.image) {
        formData.append('image', data.image);
    }
    // 3. Отправляем запрос на сервер
    try {
        const response = await fetch(`${apiURL}/main_api_app/add_recipe`, {
            method: 'POST',
            body: formData,
            // ВАЖНО: НЕ устанавливайте заголовок 'Content-Type'. Браузер сделает это автоматически с правильным boundary для multipart/form-data.
        });
        if (!response.ok) {
            const errorData = await response.json();
            // Возвращаем объект с ошибкой, чтобы клиент мог ее обработать
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }
        revalidatePath('/meals', 'layout');
        // Возвращаем успешный результат
        return {success: true, message: 'Recipe created successfully!'};
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


export async function createUnprotectedJsonData(data) {
    let apiURL = process.env.NEXT_PUBLIC_API_URL;
    try {
        const response = await fetch(`${apiURL}/main_api_app/create_message`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const errorData = await response.json();
            return {success: false, message: errorData.detail || `Server error: ${response.status}`};
        }
        revalidatePath('/messages', 'layout');
        return {success: true, message: 'Recipe created successfully!'};
    } catch (error) {
        console.error('Error submitting form:', error);
        return {success: false, message: 'Failed to connect to the server.'};
    }
}


export async function getProtectedDataTemplate() {
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

    try {
        let response = await fetch(`${mainUrl}/main_api_app/dashboard`,
            {cache: "no-cache", headers: requestHeaders});
        if (!response.ok) {
            if (response.status === 404) {
                return false;
            }
            throw new Error("Ошибка соединения с сервером.");
        }
        let result = await response.json();
        return result;
    } catch (error) {
        console.error("Ошибка при получении данных:", error);
        return false;
    }
}
