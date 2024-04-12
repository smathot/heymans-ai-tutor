import logging
import asyncio
import time
logger = logging.getLogger('heymans')


class BaseModel:
    
    supports_not_done_yet = False
    characters_per_token = 4
    
    def __init__(self, heymans, tools=None, tool_choice='auto'):
        self._heymans = heymans
        self._tools = tools
        self._tool_choice = tool_choice
        self.total_tokens_consumed = 0
        self.prompt_tokens_consumed = 0
        self.completion_tokens_consumed = 0
        
    def invalid_tool(self):
        return 'Invalid tool'
        
    def get_response(self, response) -> [str, callable]:
        return response.content
    
    def tools(self):
        return [{"type": "function", "function": t.tool_spec}
                for t in self._tools if t.tool_spec]
        
    def invoke(self, messages):
        return self._model.invoke(messages)
        
    def async_invoke(self, messages):
        return self._model.ainvoke(messages)
        
    def messages_length(self, messages):
        if isinstance(messages, str):
            return len(messages)
        return sum([len(m.content if hasattr(m, 'content') else m['content'])
                   for m in messages])

    def predict(self, messages, track_tokens=True):
        t0 = time.time()
        logger.info(f'predicting with {self.__class__} model')
        reply = self.get_response(self.invoke(messages))
        msg_len = self.messages_length(messages)
        dt = time.time() - t0
        prompt_tokens = msg_len // self.characters_per_token
        reply_len = len(reply) if isinstance(reply, str) else 0
        logger.info(f'predicting {reply_len + msg_len} took {dt} s')
        if track_tokens:
            completion_tokens = reply_len // self.characters_per_token
            total_tokens = prompt_tokens + completion_tokens
            self.total_tokens_consumed += total_tokens
            self.prompt_tokens_consumed += prompt_tokens
            self.completion_tokens_consumed += completion_tokens
            logger.info(f'total tokens (approx.): {total_tokens}')
            logger.info(f'prompt tokens (approx.): {prompt_tokens}')
            logger.info(f'completion tokens (approx.): {completion_tokens}')
        return reply
    
    def predict_multiple(self, prompts):
        """Predicts multiple simple (non-message history) prompts using asyncio
        if possible.
        """
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                logger.info('re-using async event loop')
                use_async = True
            else:
                logger.info('async event loop is already running')
                use_async = False
        except RuntimeError as e:
            logger.info('creating async event loop')
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            use_async = True
            
        if not use_async:
            logger.info('predicting multiple without async')
            return [self.get_response(self.invoke(prompt))
                                              for prompt in prompts]
            
        async def wrap_gather():
            tasks = [self.async_invoke(prompt) for prompt in prompts]
            predictions = await asyncio.gather(*tasks)
            return [self.get_response(p) for p in predictions]
            
        logger.info('predicting multiple using async')
        return loop.run_until_complete(wrap_gather())
