module.exports = async function (context, req) {
    context.res = {
        body: "Hello from Azure Functions!",
        headers: {
            'Content-Type': 'text/plain'
        }
    };
};